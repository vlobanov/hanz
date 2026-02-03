import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
POSTGRES_URL = os.getenv("POSTGRES_URL")

# LLM settings
LLM_MODEL = "gemini-3-pro-preview"

# ElevenLabs settings
ELEVENLABS_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam - clear male voice good for German
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"
