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
from database import init_database
from prompts import ROLEPLAY_START_PROMPT
from tools.voice import text_to_speech, transcribe_audio

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    user_id = user.id

    # Initialize preferences
    agent.get_preferences(user_id)

    welcome_message = f"""Hallo {user.first_name}!

Ich bin Hanz, dein Deutschlehrer! I'll help you learn German from A1 to B1 level.

Commands:
/roleplay - Start a roleplay scenario
/grammar - See tracked grammar concepts
/voice on|off - Toggle voice responses
/level A1|A2|B1 - Set your level

Just send me a message to start chatting! Du kannst auch Sprachnachrichten schicken.

Was möchtest du heute lernen?
"""
    await update.message.reply_text(welcome_message)


async def roleplay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /roleplay command - start a new roleplay scenario."""
    user_id = update.effective_user.id

    # Clear history for fresh roleplay
    agent.clear_history(user_id)

    # Get a roleplay scenario from the agent
    response = await agent.chat(user_id, ROLEPLAY_START_PROMPT)

    prefs = agent.get_preferences(user_id)
    if prefs.get("voice_enabled"):
        await send_voice_response(update, response)
    else:
        await update.message.reply_text(response)


async def grammar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /grammar command - list tracked grammar concepts."""
    from tools.grammar import list_grammar_concepts

    result = await list_grammar_concepts.ainvoke({})
    await update.message.reply_text(result)


async def voice_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /voice command."""
    user_id = update.effective_user.id
    args = context.args

    if not args:
        prefs = agent.get_preferences(user_id)
        status = "enabled" if prefs.get("voice_enabled") else "disabled"
        await update.message.reply_text(
            f"Voice responses are currently {status}.\nUse /voice on or /voice off to change."
        )
        return

    setting = args[0].lower()
    if setting == "on":
        agent.set_preference(user_id, "voice_enabled", True)
        await update.message.reply_text("Voice responses enabled! 🔊")
    elif setting == "off":
        agent.set_preference(user_id, "voice_enabled", False)
        await update.message.reply_text("Voice responses disabled. 🔇")
    else:
        await update.message.reply_text("Usage: /voice on or /voice off")


async def level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /level command."""
    user_id = update.effective_user.id
    args = context.args

    if not args:
        prefs = agent.get_preferences(user_id)
        current = prefs.get("level", "A1")
        await update.message.reply_text(
            f"Your current level is {current}.\nUse /level A1, /level A2, or /level B1 to change."
        )
        return

    new_level = args[0].upper()
    if new_level in ["A1", "A2", "B1"]:
        agent.set_preference(user_id, "level", new_level)
        # Inform the agent about the level
        await agent.chat(
            user_id, f"[System: The student's level is now {new_level}. Adjust accordingly.]"
        )
        await update.message.reply_text(f"Level set to {new_level}! 📚")
    else:
        await update.message.reply_text("Please choose A1, A2, or B1.")


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /english, /german, /mixed commands."""
    user_id = update.effective_user.id
    command = update.message.text.lower().strip("/")

    lang_map = {
        "english": "english",
        "german": "german",
        "mixed": "mixed",
    }

    if command in lang_map:
        agent.set_preference(user_id, "language", lang_map[command])
        messages = {
            "english": "I'll speak mostly English now. 🇬🇧",
            "german": "Ich spreche jetzt hauptsächlich Deutsch! 🇩🇪",
            "mixed": "I'll mix both languages! Deutsch und English! 🇩🇪🇬🇧",
        }
        await update.message.reply_text(messages[command])


async def send_voice_response(update: Update, text: str) -> None:
    """Send a voice message response."""
    try:
        audio_data = await text_to_speech(text)
        # Use spoiler to hide transcription until tapped
        caption = f"<tg-spoiler>{text[:1024]}</tg-spoiler>"
        await update.message.reply_voice(
            voice=io.BytesIO(audio_data),
            caption=caption,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error generating voice: {e}")
        # Fall back to text
        await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages."""
    user_id = update.effective_user.id
    message_text = update.message.text

    # Get response from agent
    response = await agent.chat(user_id, message_text)

    # Check if voice is enabled
    prefs = agent.get_preferences(user_id)
    if prefs.get("voice_enabled"):
        await send_voice_response(update, response)
    else:
        await update.message.reply_text(response)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages."""
    user_id = update.effective_user.id

    # Download the voice message
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".oga", delete=False) as temp_file:
        await file.download_to_drive(temp_file.name)
        temp_path = temp_file.name

    try:
        # Transcribe using Gemini
        transcription = await transcribe_audio(temp_path)

        # Show transcription to user
        await update.message.reply_text(f"🎤 Ich habe gehört: \"{transcription}\"")

        # Process with agent
        response = await agent.chat(user_id, transcription)

        # Check if voice is enabled
        prefs = agent.get_preferences(user_id)
        if prefs.get("voice_enabled"):
            await send_voice_response(update, response)
        else:
            await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await update.message.reply_text(
            "Entschuldigung, ich konnte die Sprachnachricht nicht verstehen. "
            "Kannst du es nochmal versuchen oder als Text schreiben?"
        )
    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


async def post_init(application: Application) -> None:
    """Initialize database after application starts."""
    await init_database()
    logger.info("Database initialized")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("roleplay", roleplay))
    application.add_handler(CommandHandler("grammar", grammar))
    application.add_handler(CommandHandler("voice", voice_setting))
    application.add_handler(CommandHandler("level", level))
    application.add_handler(CommandHandler("english", set_language))
    application.add_handler(CommandHandler("german", set_language))
    application.add_handler(CommandHandler("mixed", set_language))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Start the bot
    logger.info("Starting Hanz German Tutor Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
