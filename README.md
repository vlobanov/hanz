# Hanz - German Learning Telegram Bot

A Telegram bot that acts as a German language tutor for A1-B1 learners. Features conversational practice, immersive roleplays, voice messages, and grammar tracking.

## Features

- **Conversational Practice** - Chat in German with adaptive difficulty based on your level
- **Immersive Roleplays** - Practice real-life scenarios (apartment hunting, job interviews, ordering at a restaurant) where Hanz plays a German-speaking character
- **Voice Input** - Send voice messages, Hanz transcribes and responds
- **Voice Output** - Receive responses as voice messages with hidden transcription (tap to reveal)
- **Grammar Tracking** - Hanz tracks grammar concepts you're learning in a local database

## Tech Stack

- **python-telegram-bot** - Telegram integration
- **LangChain + LangGraph** - Agent orchestration with tools
- **Google Gemini** - LLM for conversations and voice transcription
- **ElevenLabs** - Text-to-speech for voice messages
- **SQLite** - Grammar concepts storage

## Setup

1. Clone and install dependencies:
```bash
cd hanz
uv sync
```

2. Copy `.env.example` to `.env` and fill in your API keys:
```
TELEGRAM_BOT_TOKEN=     # From @BotFather on Telegram
GOOGLE_API_KEY=         # From Google AI Studio
ELEVENLABS_API_KEY=     # From ElevenLabs
```

3. Run the bot:
```bash
uv run python bot.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and command list |
| `/roleplay` | Start a new roleplay scenario |
| `/grammar` | List tracked grammar concepts |
| `/voice on` | Enable voice responses |
| `/voice off` | Disable voice responses |
| `/level A1\|A2\|B1` | Set your German level |

## Roleplay Scenarios

When you use `/roleplay`, Hanz becomes a German-speaking character in scenarios like:

- **Wohnungssuche** - A difficult landlord asking many questions
- **Vorstellungsgespräch** - A strict HR manager interviewing you
- **Im Biergarten** - An impatient waiter taking your order
- **Arztbesuch** - A doctor asking about your symptoms
- **Nachbarschaftsstreit** - A neighbor complaining about noise
- **Dating** - A curious date asking questions

You must respond in German to continue the conversation. Hanz stays in character but gives periodic feedback on your mistakes.

## Project Structure

```
hanz/
├── bot.py           # Telegram handlers and main entry point
├── agent.py         # LangChain agent with grammar tools
├── config.py        # Environment variables
├── database.py      # SQLite for grammar tracking
├── prompts.py       # System prompts for the tutor
└── tools/
    ├── grammar.py   # Grammar tracking tools (save/update/list/master)
    └── voice.py     # ElevenLabs TTS, Gemini STT
```

## How It Works

1. **Text messages** → Sent to Gemini via LangChain agent → Response sent back
2. **Voice messages** → Downloaded → Transcribed by Gemini → Processed by agent → Response sent back
3. **Voice responses** → Agent response → ElevenLabs TTS → Sent as Telegram voice message with spoiler transcription

The agent has access to tools for tracking grammar concepts. When it introduces a new concept (like Akkusativ or Perfekt), it can save it to the database. You can view tracked concepts with `/grammar`.
