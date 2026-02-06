import io
import logging
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agent import agent
from config import TELEGRAM_BOT_TOKEN
from database import (
    init_database,
    get_user_state,
    update_user_state,
    get_all_progress,
    add_vocabulary_words,
    get_vocabulary_stats,
    add_grammar_topics,
    get_grammar_stats,
)
from prompts import ROLEPLAY_START_PROMPT, START_DAY_PROMPT, REVIEW_PROMPT
from study_plan import get_day_title, get_all_days_summary
from tools.voice import text_to_speech, transcribe_audio, set_telegram_context

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def agent_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message: str) -> str:
    """Chat with agent, setting Telegram context so voice tools can send messages."""
    set_telegram_context(context.bot, update.effective_chat.id)
    return await agent.chat(user_id, message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """Hanz B1 Exam Prep - Commands

STUDY:
/day - Start today's lesson
/day N - Jump to day N (e.g. /day 5)
/done - Mark current day as completed
/progress - Show your 20-day progress

VOCABULARY:
/memo word1 word2 - Add words to memorize
/memo - Show vocabulary stats
/words - Practice vocabulary with sentences

GRAMMAR:
/grammar topic1 topic2 - Add grammar topics
/grammar - Show grammar stats
/drill - Rapid-fire grammar practice

PRACTICE:
/review - Review weak topics from lessons
/roleplay - Fun conversation practice

SETTINGS:
/voice on - Enable voice responses
/voice off - Disable voice responses

OTHER:
/start - Welcome message
/help - This help

Say "stop" or "fertig" to end drills.
"""
    await update.message.reply_text(help_text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    user_id = user.id

    # Initialize user state
    state = await get_user_state(user_id)
    progress = await get_all_progress(user_id)
    completed = sum(1 for p in progress if p["status"] == "completed")

    welcome_message = f"""Hallo {user.first_name}!

Ich bin Hanz, dein B1-Prüfungscoach! Ich helfe dir in 20 Tagen, dich auf die B1-Prüfung vorzubereiten.

Dein Fortschritt: {completed}/20 Tage abgeschlossen
Aktueller Tag: {state['current_day']}

Commands:
/day - Starte den aktuellen Tag ({state['current_day']})
/day N - Springe zu Tag N (z.B. /day 5)
/progress - Zeige deinen Gesamtfortschritt
/review - Wiederhole schwierige Themen
/roleplay - Übe mit einem lustigen Rollenspiel
/voice on|off - Sprachnachrichten an/aus
/done - Markiere den aktuellen Tag als fertig

Los geht's! Schreib /day um mit Tag {state['current_day']} zu beginnen.
"""
    await update.message.reply_text(welcome_message)


async def day_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /day command - start or continue a study day."""
    user_id = update.effective_user.id
    state = await get_user_state(user_id)

    # Check if a specific day was requested
    if context.args:
        try:
            day_number = int(context.args[0])
            if day_number < 1 or day_number > 20:
                await update.message.reply_text("Bitte wähle einen Tag zwischen 1 und 20.")
                return
        except ValueError:
            await update.message.reply_text("Bitte gib eine Zahl ein, z.B. /day 5")
            return
    else:
        day_number = state["current_day"]

    # Update current day
    await update_user_state(user_id, current_day=day_number, current_mode="study")

    # Clear history for fresh day
    agent.clear_history(user_id)

    # Start the day with the agent
    prompt = START_DAY_PROMPT.format(day_number=day_number, user_id=user_id)
    response = await agent_chat(update, context, user_id, prompt)

    await send_response(update, user_id, response)


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /progress command - show study progress."""
    user_id = update.effective_user.id

    progress = await get_all_progress(user_id)
    all_days = get_all_days_summary()

    progress_map = {p["day_number"]: p["status"] for p in progress}

    result = "Dein Lernfortschritt:\n\n"

    current_week = 0
    for day_info in all_days:
        day_num = day_info["day"]
        if day_info["week"] != current_week:
            current_week = day_info["week"]
            result += f"\n--- Woche {current_week} ---\n"

        status = progress_map.get(day_num, "not_started")
        icon = {"completed": "✅", "in_progress": "🔄", "not_started": "⬜"}.get(status, "⬜")
        result += f"{icon} Tag {day_num}: {day_info['title']}\n"

    completed = sum(1 for p in progress if p["status"] == "completed")
    result += f"\nAbgeschlossen: {completed}/20 Tage"

    await update.message.reply_text(result)


async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /review command - review weak topics."""
    user_id = update.effective_user.id

    await update_user_state(user_id, current_mode="review")
    agent.clear_history(user_id)

    prompt = REVIEW_PROMPT.format(user_id=user_id)
    response = await agent_chat(update, context, user_id, prompt)

    await send_response(update, user_id, response)


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /done command - mark current day as completed."""
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    current_day = state["current_day"]

    # Ask agent to mark day complete
    response = await agent_chat(
        update, context, user_id,
        f"Der Schüler sagt, er ist fertig mit Tag {current_day}. "
        f"Markiere den Tag als abgeschlossen mit mark_day_completed (user_id: {user_id}, day_number: {current_day}). "
        f"Gratuliere und schlage vor, morgen mit Tag {current_day + 1} weiterzumachen."
    )

    # Move to next day
    if current_day < 20:
        await update_user_state(user_id, current_day=current_day + 1)

    await send_response(update, user_id, response)


async def roleplay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /roleplay command - start a fun roleplay scenario."""
    user_id = update.effective_user.id

    await update_user_state(user_id, current_mode="roleplay")
    agent.clear_history(user_id)

    response = await agent_chat(update, context, user_id, ROLEPLAY_START_PROMPT)

    await send_response(update, user_id, response)


async def memo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /memo command - add words to vocabulary (does NOT go to agent)."""
    user_id = update.effective_user.id

    if not context.args:
        stats = await get_vocabulary_stats(user_id)
        await update.message.reply_text(
            f"Dein Vokabular: {stats['total']} Wörter\n"
            f"Gut gelernt: {stats['learned']}\n"
            f"Zur Wiederholung: {stats['due_for_review']}\n\n"
            "Benutze: /memo wort1 wort2 wort3 ..."
        )
        return

    words = context.args
    added = await add_vocabulary_words(user_id, words)

    if added == 0:
        await update.message.reply_text("Diese Wörter sind schon in deiner Liste.")
    elif added == 1:
        await update.message.reply_text(f"'{words[0]}' hinzugefügt!")
    else:
        await update.message.reply_text(f"{added} Wörter hinzugefügt!")


async def words_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /words command - practice vocabulary."""
    user_id = update.effective_user.id

    await update_user_state(user_id, current_mode="words")
    agent.clear_history(user_id)

    prompt = f"""Der Schüler möchte Vokabeln üben.

1. Hole die Wörter mit get_practice_words (user_id: {user_id})
2. Wenn es Wörter gibt, wähle eins aus und:
   - Gib die deutsche Übersetzung/Erklärung
   - Bitte den Schüler, einen kurzen Satz mit dem Wort zu bilden
3. Wenn der Schüler antwortet, bewerte ob der Satz korrekt ist
4. Benutze mark_word_practiced mit correct=true/false
5. Dann das nächste Wort

Mach es interaktiv - ein Wort nach dem anderen!
"""
    response = await agent_chat(update, context, user_id, prompt)
    await send_response(update, user_id, response)


async def grammar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /grammar command - add grammar topics (does NOT go to agent)."""
    user_id = update.effective_user.id

    if not context.args:
        stats = await get_grammar_stats(user_id)
        await update.message.reply_text(
            f"Grammatik-Themen: {stats['total']}\n"
            f"Gemeistert: {stats['learned']}\n"
            f"Zum Üben: {stats['due_for_review']}\n\n"
            "Benutze: /grammar thema1 thema2 ...\n"
            "Beispiele: /grammar perfekt akkusativ konjunktiv"
        )
        return

    # Join args to allow multi-word topics separated by commas
    text = " ".join(context.args)
    topics = [t.strip() for t in text.replace(",", " ").split() if t.strip()]

    added = await add_grammar_topics(user_id, topics)

    if added == 0:
        await update.message.reply_text("Diese Themen sind schon in deiner Liste.")
    elif added == 1:
        await update.message.reply_text(f"'{topics[0]}' hinzugefügt!")
    else:
        await update.message.reply_text(f"{added} Themen hinzugefügt!")


async def drill_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /drill command - rapid-fire grammar practice."""
    user_id = update.effective_user.id

    await update_user_state(user_id, current_mode="drill")
    agent.clear_history(user_id)

    prompt = f"""RAPID-FIRE GRAMMATIK-DRILL!

1. Hole die Themen mit get_grammar_drill_topics (user_id: {user_id})
2. Für jedes Thema, stelle SCHNELLE Übungen:

Für Verb-Konjugation:
- "Konjugiere 'sein' für 'wir':" -> wir sind
- "Perfekt von 'gehen':" -> gegangen
- "'haben' im Präteritum, ich:" -> ich hatte

Für Kasus:
- "Akkusativ: der Hund -> ?" -> den Hund
- "Mit + Dativ: die Frau -> ?" -> mit der Frau

Für andere Themen:
- Stelle passende kurze Übungen

FORMAT:
- Eine Frage stellen
- Auf Antwort warten
- KURZ korrigieren (Richtig! oder Falsch: X ist Y)
- mark_grammar_attempt aufrufen
- Nächste Frage SOFORT

Mach es SCHNELL - keine langen Erklärungen! Nur Frage -> Antwort -> Feedback -> Nächste.
Wenn der Schüler "stop" oder "fertig" sagt, beende das Drill.
"""
    response = await agent_chat(update, context, user_id, prompt)
    await send_response(update, user_id, response)


async def voice_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /voice command."""
    user_id = update.effective_user.id
    args = context.args

    state = await get_user_state(user_id)

    if not args:
        status = "an" if state.get("voice_enabled") else "aus"
        await update.message.reply_text(
            f"Sprachnachrichten sind aktuell {status}.\n"
            "Benutze /voice on oder /voice off zum Ändern."
        )
        return

    setting = args[0].lower()
    if setting == "on":
        await update_user_state(user_id, voice_enabled=1)
        await update.message.reply_text("Sprachnachrichten aktiviert! 🔊")
    elif setting == "off":
        await update_user_state(user_id, voice_enabled=0)
        await update.message.reply_text("Sprachnachrichten deaktiviert. 🔇")
    else:
        await update.message.reply_text("Benutze: /voice on oder /voice off")


async def send_response(update: Update, user_id: int, text: str) -> None:
    """Send response as text or voice based on user preference."""
    state = await get_user_state(user_id)

    if state.get("voice_enabled"):
        await send_voice_response(update, text)
    else:
        await update.message.reply_text(text)


async def send_voice_response(update: Update, text: str) -> None:
    """Send a voice message response."""
    try:
        audio_data = await text_to_speech(text)
        caption = f"<tg-spoiler>{text[:1024]}</tg-spoiler>"
        await update.message.reply_voice(
            voice=io.BytesIO(audio_data),
            caption=caption,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error generating voice: {e}")
        await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages."""
    user_id = update.effective_user.id
    message_text = update.message.text

    response = await agent_chat(update, context, user_id, message_text)

    await send_response(update, user_id, response)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages."""
    user_id = update.effective_user.id

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".oga", delete=False) as temp_file:
        await file.download_to_drive(temp_file.name)
        temp_path = temp_file.name

    try:
        transcription = await transcribe_audio(temp_path)
        await update.message.reply_text(f"🎤 Ich habe gehört: \"{transcription}\"")

        response = await agent_chat(update, context, user_id, transcription)
        await send_response(update, user_id, response)

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await update.message.reply_text(
            "Entschuldigung, ich konnte die Sprachnachricht nicht verstehen. "
            "Kannst du es nochmal versuchen oder als Text schreiben?"
        )
    finally:
        Path(temp_path).unlink(missing_ok=True)


async def post_init(application: Application) -> None:
    """Initialize database after application starts."""
    await init_database()
    logger.info("Database initialized")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("day", day_command))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("review", review_command))
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("roleplay", roleplay))
    application.add_handler(CommandHandler("memo", memo_command))
    application.add_handler(CommandHandler("words", words_command))
    application.add_handler(CommandHandler("grammar", grammar_command))
    application.add_handler(CommandHandler("drill", drill_command))
    application.add_handler(CommandHandler("voice", voice_setting))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("Starting Hanz B1 Exam Prep Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
