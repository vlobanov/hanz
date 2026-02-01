import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# LLM settings
LLM_MODEL = "gemini-2.0-flash"

# ElevenLabs settings
ELEVENLABS_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam - clear male voice good for German
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"

# Database
DATABASE_PATH = "hanz.db"
