from langchain_core.tools import tool
from database import (
    get_day_progress,
    start_day,
    complete_day,
    get_all_progress,
    add_review_note,
    get_review_notes,
    mark_note_reviewed,
    get_words_for_practice,
    get_all_vocabulary,
    record_word_practice,
    get_vocabulary_stats,
    get_grammar_for_practice,
    get_all_grammar_topics,
    record_grammar_practice,
    get_grammar_stats,
)
from study_plan import get_day, get_day_title, get_all_days_summary


@tool
async def get_study_day_content(day_number: int) -> str:
    """Get the full content for a specific study day.

    Use this to retrieve grammar explanations, key phrases, exercises,
    and speaking prompts for a given day in the 20-day B1 exam prep plan.

    Args:
        day_number: The day number (1-20)
    """
    day = get_day(day_number)
    if not day:
        return f"Day {day_number} not found. Valid days are 1-20."

    content = f"DAY {day_number}: {day['title']} (Week {day['week']})\n\n"
    content += "=== GRAMMAR ===\n"
    content += day["grammar"].strip() + "\n\n"
    content += "=== KEY PHRASES ===\n"
    for phrase in day["key_phrases"]:
        content += f"- {phrase}\n"
    content += "\n=== EXERCISES ===\n"
    for i, ex in enumerate(day["exercises"], 1):
        content += f"{i}. {ex}\n"
    content += "\n=== SPEAKING PROMPTS ===\n"
    for prompt in day["speaking_prompts"]:
        content += f"- {prompt}\n"

    return content


@tool
async def mark_day_started(user_id: int, day_number: int) -> str:
    """Mark a study day as started/in progress.

    Use this when the student begins working on a specific day.

    Args:
        user_id: The Telegram user ID
        day_number: The day number (1-20)
    """
    await start_day(user_id, day_number)
    title = get_day_title(day_number)
    return f"Started Day {day_number}: {title}"


@tool
async def mark_day_completed(user_id: int, day_number: int) -> str:
    """Mark a study day as completed.

    Use this when the student has finished all exercises and speaking practice for a day.

    Args:
        user_id: The Telegram user ID
        day_number: The day number (1-20)
    """
    await complete_day(user_id, day_number)
    title = get_day_title(day_number)
    return f"Completed Day {day_number}: {title}! Great work!"


@tool
async def get_study_progress(user_id: int) -> str:
    """Get the student's overall study progress.

    Shows which days are completed, in progress, or not started.

    Args:
        user_id: The Telegram user ID
    """
    progress = await get_all_progress(user_id)
    all_days = get_all_days_summary()

    progress_map = {p["day_number"]: p["status"] for p in progress}

    result = "Study Progress (20 days total):\n\n"

    current_week = 0
    for day_info in all_days:
        day_num = day_info["day"]
        if day_info["week"] != current_week:
            current_week = day_info["week"]
            result += f"\n--- Week {current_week} ---\n"

        status = progress_map.get(day_num, "not_started")
        icon = {"completed": "✅", "in_progress": "🔄", "not_started": "⬜"}.get(status, "⬜")
        result += f"{icon} Day {day_num}: {day_info['title']}\n"

    completed = sum(1 for p in progress if p["status"] == "completed")
    result += f"\nCompleted: {completed}/20 days"

    return result


@tool
async def add_topic_to_review(
    user_id: int, topic: str, note: str = None, day_number: int = None, priority: str = "medium"
) -> str:
    """Add a topic that needs review later.

    Use this when the student struggles with a concept or makes repeated mistakes.
    This helps track weak areas for future practice.

    Args:
        user_id: The Telegram user ID
        topic: The grammar topic or concept (e.g., "Perfekt with sein", "wenn vs ob")
        note: Optional details about what was difficult
        day_number: Optional day number where this came up
        priority: Priority level - "high", "medium", or "low"
    """
    if priority not in ["high", "medium", "low"]:
        priority = "medium"

    note_id = await add_review_note(user_id, topic, note, day_number, priority)
    return f"Added '{topic}' to review list (priority: {priority}). I'll remind you to practice this later."


@tool
async def get_topics_to_review(user_id: int) -> str:
    """Get all topics marked for review.

    Use this to see what the student needs to practice more.

    Args:
        user_id: The Telegram user ID
    """
    notes = await get_review_notes(user_id, include_reviewed=False)

    if not notes:
        return "No topics marked for review. Great job!"

    result = "Topics to review:\n\n"

    priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    for note in notes:
        icon = priority_icons.get(note["priority"], "🟡")
        result += f"{icon} [{note['id']}] {note['topic']}"
        if note["day_number"]:
            result += f" (from Day {note['day_number']})"
        if note["note"]:
            result += f"\n   Note: {note['note']}"
        result += "\n"

    return result


@tool
async def mark_topic_reviewed(note_id: int) -> str:
    """Mark a review topic as reviewed/practiced.

    Use this when the student has successfully practiced a weak topic.

    Args:
        note_id: The ID of the review note
    """
    await mark_note_reviewed(note_id)
    return f"Marked topic #{note_id} as reviewed!"


@tool
async def get_practice_words(user_id: int) -> str:
    """Get vocabulary words due for practice.

    Returns words that need review, prioritizing those the student struggles with.

    Args:
        user_id: The Telegram user ID
    """
    words = await get_words_for_practice(user_id, limit=5)

    if not words:
        stats = await get_vocabulary_stats(user_id)
        if stats["total"] == 0:
            return "No vocabulary words yet. The student can add words with /memo word1 word2 ..."
        return "No words due for review right now. All caught up!"

    result = "Words to practice:\n"
    for w in words:
        success = ""
        if w["times_practiced"] > 0:
            rate = w["times_correct"] / w["times_practiced"] * 100
            success = f" ({rate:.0f}% correct)"
        result += f"- [ID:{w['id']}] {w['word']}{success}\n"

    return result


@tool
async def mark_word_practiced(word_id: int, correct: bool) -> str:
    """Record whether the student got a word correct in practice.

    This updates the spaced repetition schedule for the word.

    Args:
        word_id: The ID of the vocabulary word
        correct: True if the student used the word correctly, False otherwise
    """
    await record_word_practice(word_id, correct)
    if correct:
        return f"Correct! Word #{word_id} marked as successful."
    return f"Word #{word_id} needs more practice. Will review again soon."


@tool
async def get_vocab_stats(user_id: int) -> str:
    """Get vocabulary statistics for the student.

    Args:
        user_id: The Telegram user ID
    """
    stats = await get_vocabulary_stats(user_id)
    return (
        f"Vocabulary Stats:\n"
        f"- Total words: {stats['total']}\n"
        f"- Well learned (80%+ correct): {stats['learned']}\n"
        f"- Due for review: {stats['due_for_review']}"
    )


@tool
async def get_grammar_drill_topics(user_id: int) -> str:
    """Get grammar topics due for drill practice.

    Returns topics that need practice, prioritizing those the student struggles with.

    Args:
        user_id: The Telegram user ID
    """
    topics = await get_grammar_for_practice(user_id, limit=3)

    if not topics:
        stats = await get_grammar_stats(user_id)
        if stats["total"] == 0:
            return "No grammar topics yet. The student can add topics with /grammar topic1 topic2 ..."
        return "No grammar topics due for review right now!"

    result = "Grammar topics to drill:\n"
    for t in topics:
        success = ""
        if t["times_practiced"] > 0:
            rate = t["times_correct"] / t["times_practiced"] * 100
            success = f" ({rate:.0f}% correct, {t['times_practiced']} attempts)"
        result += f"- [ID:{t['id']}] {t['topic']}{success}\n"

    return result


@tool
async def mark_grammar_attempt(topic_id: int, correct: bool) -> str:
    """Record whether the student got a grammar drill correct.

    Args:
        topic_id: The ID of the grammar topic
        correct: True if correct, False otherwise
    """
    await record_grammar_practice(topic_id, correct)
    if correct:
        return f"Richtig! Grammar topic #{topic_id} marked correct."
    return f"Grammar topic #{topic_id} needs more practice."


@tool
async def get_grammar_practice_stats(user_id: int) -> str:
    """Get grammar practice statistics.

    Args:
        user_id: The Telegram user ID
    """
    stats = await get_grammar_stats(user_id)
    return (
        f"Grammar Stats:\n"
        f"- Total topics: {stats['total']}\n"
        f"- Mastered (80%+ over 10+ attempts): {stats['learned']}\n"
        f"- Due for drill: {stats['due_for_review']}"
    )


def get_study_tools():
    """Return all study-related tools for the agent."""
    return [
        get_study_day_content,
        mark_day_started,
        mark_day_completed,
        get_study_progress,
        add_topic_to_review,
        get_topics_to_review,
        mark_topic_reviewed,
        get_practice_words,
        mark_word_practiced,
        get_vocab_stats,
        get_grammar_drill_topics,
        mark_grammar_attempt,
        get_grammar_practice_stats,
    ]
