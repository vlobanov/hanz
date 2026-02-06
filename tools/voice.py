import contextvars
import io

from google import genai
from elevenlabs import ElevenLabs
from langchain_core.tools import tool

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    ELEVENLABS_MODEL_ID,
    GOOGLE_API_KEY,
)

# Context vars for passing Telegram bot/chat into agent tools
_telegram_bot: contextvars.ContextVar = contextvars.ContextVar("telegram_bot")
_telegram_chat_id: contextvars.ContextVar = contextvars.ContextVar("telegram_chat_id")


def set_telegram_context(bot, chat_id: int) -> None:
    """Set Telegram context for voice tools. Call before agent.chat()."""
    _telegram_bot.set(bot)
    _telegram_chat_id.set(chat_id)


def _get_elevenlabs_client() -> ElevenLabs:
    """Get ElevenLabs client."""
    return ElevenLabs(api_key=ELEVENLABS_API_KEY)


def _get_genai_client() -> genai.Client:
    """Get Google GenAI client."""
    return genai.Client(api_key=GOOGLE_API_KEY)


async def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file using Gemini multimodal.

    Args:
        audio_path: Path to the audio file (typically .oga from Telegram)

    Returns:
        Transcribed text from the audio
    """
    client = _get_genai_client()

    # Upload the audio file to Gemini
    audio_file = client.files.upload(file=audio_path)

    # Use Gemini to transcribe
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            audio_file,
            "Transcribe this audio exactly as spoken. The speaker is learning German, "
            "so the audio may contain German, English, or a mix of both. "
            "Return only the transcription, nothing else.",
        ],
    )

    return response.text.strip()


async def text_to_speech(text: str) -> bytes:
    """Convert text to speech using ElevenLabs.

    Args:
        text: Text to convert to speech (German or English)

    Returns:
        Audio data as bytes in OGG format (suitable for Telegram voice messages)
    """
    client = _get_elevenlabs_client()

    # Generate audio using ElevenLabs with opus format (works with Telegram voice)
    audio_generator = client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        model_id=ELEVENLABS_MODEL_ID,
        text=text,
        output_format="opus_48000_64",
    )

    # Collect all audio chunks
    audio_data = b"".join(audio_generator)

    return audio_data


@tool
async def send_voice_message(text: str) -> str:
    """Send a voice message to the student using text-to-speech.

    Use this to proactively send voice exercises: dictation, listening comprehension,
    grammar drills, or any content the student should hear spoken aloud.
    The text will be converted to natural German speech and sent as a Telegram voice message.

    Args:
        text: The text to speak (German or English)
    """
    try:
        bot = _telegram_bot.get()
        chat_id = _telegram_chat_id.get()
    except LookupError:
        return "Error: Telegram context not available. Cannot send voice message."

    audio_data = await text_to_speech(text)
    caption = f"<tg-spoiler>{text[:1024]}</tg-spoiler>"
    await bot.send_voice(
        chat_id=chat_id,
        voice=io.BytesIO(audio_data),
        caption=caption,
        parse_mode="HTML",
    )
    return "Voice message sent successfully."


def get_voice_tools():
    """Return all voice-related tools for the agent."""
    return [send_voice_message]
