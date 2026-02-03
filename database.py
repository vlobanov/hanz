import asyncpg
from datetime import datetime, timedelta
from config import POSTGRES_URL

# Connection pool
_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get or create connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(POSTGRES_URL)
    return _pool


async def init_database():
    """Initialize database connection pool."""
    await get_pool()


# User state functions
async def get_user_state(user_id: int) -> dict:
    """Get or create user state."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM user_state WHERE user_id = $1", user_id
        )

        if row:
            return dict(row)

        # Create new user state
        await conn.execute(
            """INSERT INTO user_state (user_id, current_day, current_mode, voice_enabled)
               VALUES ($1, 1, 'study', FALSE)
               ON CONFLICT (user_id) DO NOTHING""",
            user_id,
        )
        return {
            "user_id": user_id,
            "current_day": 1,
            "current_mode": "study",
            "voice_enabled": False,
        }


async def update_user_state(user_id: int, **kwargs) -> None:
    """Update user state fields."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Ensure user exists
        await get_user_state(user_id)

        updates = []
        values = []
        param_idx = 1

        for key, value in kwargs.items():
            if key in ("current_day", "current_mode", "voice_enabled"):
                updates.append(f"{key} = ${param_idx}")
                values.append(value)
                param_idx += 1

        if updates:
            updates.append(f"updated_at = ${param_idx}")
            values.append(datetime.now())
            param_idx += 1
            values.append(user_id)

            await conn.execute(
                f"UPDATE user_state SET {', '.join(updates)} WHERE user_id = ${param_idx}",
                *values,
            )


# Study progress functions
async def get_day_progress(user_id: int, day_number: int) -> dict | None:
    """Get progress for a specific day."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM study_progress WHERE user_id = $1 AND day_number = $2",
            user_id, day_number,
        )
        return dict(row) if row else None


async def start_day(user_id: int, day_number: int) -> None:
    """Mark a day as started."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO study_progress (user_id, day_number, status, started_at)
               VALUES ($1, $2, 'in_progress', $3)
               ON CONFLICT (user_id, day_number)
               DO UPDATE SET status = 'in_progress', started_at = $3""",
            user_id, day_number, datetime.now(),
        )


async def complete_day(user_id: int, day_number: int) -> None:
    """Mark a day as completed."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE study_progress SET status = 'completed', completed_at = $1
               WHERE user_id = $2 AND day_number = $3""",
            datetime.now(), user_id, day_number,
        )


async def get_all_progress(user_id: int) -> list[dict]:
    """Get all study progress for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM study_progress WHERE user_id = $1 ORDER BY day_number",
            user_id,
        )
        return [dict(row) for row in rows]


# Review notes functions
async def add_review_note(
    user_id: int, topic: str, note: str = None, day_number: int = None, priority: str = "medium"
) -> int:
    """Add a topic to review later."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO review_notes (user_id, day_number, topic, note, priority)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING id""",
            user_id, day_number, topic, note, priority,
        )
        return row["id"]


async def get_review_notes(user_id: int, include_reviewed: bool = False) -> list[dict]:
    """Get all review notes for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if include_reviewed:
            rows = await conn.fetch(
                """SELECT * FROM review_notes WHERE user_id = $1
                   ORDER BY priority DESC, created_at DESC""",
                user_id,
            )
        else:
            rows = await conn.fetch(
                """SELECT * FROM review_notes WHERE user_id = $1 AND reviewed = FALSE
                   ORDER BY priority DESC, created_at DESC""",
                user_id,
            )
        return [dict(row) for row in rows]


async def mark_note_reviewed(note_id: int) -> None:
    """Mark a review note as reviewed."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE review_notes SET reviewed = TRUE WHERE id = $1", note_id
        )


# Vocabulary functions
async def add_vocabulary_words(user_id: int, words: list[str]) -> int:
    """Add words to vocabulary list. Returns count of new words added."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        added = 0
        for word in words:
            word = word.strip().lower()
            if not word:
                continue
            result = await conn.execute(
                """INSERT INTO vocabulary (user_id, word)
                   VALUES ($1, $2)
                   ON CONFLICT (user_id, word) DO NOTHING""",
                user_id, word,
            )
            if result == "INSERT 0 1":
                added += 1
        return added


async def get_words_for_practice(user_id: int, limit: int = 5) -> list[dict]:
    """Get words due for practice, prioritizing those due for review."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT * FROM vocabulary
               WHERE user_id = $1 AND next_review <= NOW()
               ORDER BY
                   CASE WHEN times_practiced = 0 THEN 0
                        ELSE times_correct::FLOAT / times_practiced END ASC,
                   next_review ASC
               LIMIT $2""",
            user_id, limit,
        )
        return [dict(row) for row in rows]


async def get_all_vocabulary(user_id: int) -> list[dict]:
    """Get all vocabulary words for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM vocabulary WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )
        return [dict(row) for row in rows]


async def record_word_practice(word_id: int, correct: bool) -> None:
    """Record a practice attempt for a word and calculate next review time."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT times_practiced, times_correct FROM vocabulary WHERE id = $1",
            word_id,
        )
        if not row:
            return

        times_practiced = row["times_practiced"] + 1
        times_correct = row["times_correct"] + (1 if correct else 0)

        # Calculate next review interval based on success rate
        success_rate = times_correct / times_practiced if times_practiced > 0 else 0

        if success_rate >= 0.9 and times_practiced >= 5:
            next_review = datetime.now() + timedelta(days=7)
        elif success_rate >= 0.7:
            next_review = datetime.now() + timedelta(days=3)
        elif success_rate >= 0.5:
            next_review = datetime.now() + timedelta(days=1)
        else:
            next_review = datetime.now() + timedelta(hours=4)

        await conn.execute(
            """UPDATE vocabulary
               SET times_practiced = $1, times_correct = $2, last_practiced = $3, next_review = $4
               WHERE id = $5""",
            times_practiced, times_correct, datetime.now(), next_review, word_id,
        )


async def get_vocabulary_stats(user_id: int) -> dict:
    """Get vocabulary statistics for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM vocabulary WHERE user_id = $1", user_id
        )

        learned = await conn.fetchval(
            """SELECT COUNT(*) FROM vocabulary
               WHERE user_id = $1 AND times_practiced >= 5
               AND times_correct::FLOAT / NULLIF(times_practiced, 0) >= 0.8""",
            user_id,
        )

        due = await conn.fetchval(
            "SELECT COUNT(*) FROM vocabulary WHERE user_id = $1 AND next_review <= NOW()",
            user_id,
        )

        return {"total": total or 0, "learned": learned or 0, "due_for_review": due or 0}


# Grammar topics functions
async def add_grammar_topics(user_id: int, topics: list[str]) -> int:
    """Add grammar topics to practice. Returns count of new topics added."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        added = 0
        for topic in topics:
            topic = topic.strip().lower()
            if not topic:
                continue
            result = await conn.execute(
                """INSERT INTO grammar_topics (user_id, topic)
                   VALUES ($1, $2)
                   ON CONFLICT (user_id, topic) DO NOTHING""",
                user_id, topic,
            )
            if result == "INSERT 0 1":
                added += 1
        return added


async def get_grammar_for_practice(user_id: int, limit: int = 3) -> list[dict]:
    """Get grammar topics due for practice."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT * FROM grammar_topics
               WHERE user_id = $1 AND next_review <= NOW()
               ORDER BY
                   CASE WHEN times_practiced = 0 THEN 0
                        ELSE times_correct::FLOAT / times_practiced END ASC,
                   next_review ASC
               LIMIT $2""",
            user_id, limit,
        )
        return [dict(row) for row in rows]


async def get_all_grammar_topics(user_id: int) -> list[dict]:
    """Get all grammar topics for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM grammar_topics WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )
        return [dict(row) for row in rows]


async def record_grammar_practice(topic_id: int, correct: bool) -> None:
    """Record a practice attempt for a grammar topic."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT times_practiced, times_correct FROM grammar_topics WHERE id = $1",
            topic_id,
        )
        if not row:
            return

        times_practiced = row["times_practiced"] + 1
        times_correct = row["times_correct"] + (1 if correct else 0)

        # Calculate next review interval
        success_rate = times_correct / times_practiced if times_practiced > 0 else 0

        if success_rate >= 0.9 and times_practiced >= 10:
            next_review = datetime.now() + timedelta(days=7)
        elif success_rate >= 0.7:
            next_review = datetime.now() + timedelta(days=2)
        elif success_rate >= 0.5:
            next_review = datetime.now() + timedelta(days=1)
        else:
            next_review = datetime.now() + timedelta(hours=2)

        await conn.execute(
            """UPDATE grammar_topics
               SET times_practiced = $1, times_correct = $2, last_practiced = $3, next_review = $4
               WHERE id = $5""",
            times_practiced, times_correct, datetime.now(), next_review, topic_id,
        )


async def get_grammar_stats(user_id: int) -> dict:
    """Get grammar practice statistics."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM grammar_topics WHERE user_id = $1", user_id
        )

        learned = await conn.fetchval(
            """SELECT COUNT(*) FROM grammar_topics
               WHERE user_id = $1 AND times_practiced >= 10
               AND times_correct::FLOAT / NULLIF(times_practiced, 0) >= 0.8""",
            user_id,
        )

        due = await conn.fetchval(
            "SELECT COUNT(*) FROM grammar_topics WHERE user_id = $1 AND next_review <= NOW()",
            user_id,
        )

        return {"total": total or 0, "learned": learned or 0, "due_for_review": due or 0}
