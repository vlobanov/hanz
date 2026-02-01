from google import genai
from elevenlabs import ElevenLabs

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    ELEVENLABS_MODEL_ID,
    GOOGLE_API_KEY,
)


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
