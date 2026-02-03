# Hanz - B1 German Exam Prep Bot

A Telegram bot that guides you through a structured 20-day B1 exam preparation plan. Features daily lessons with grammar, exercises, speaking practice, progress tracking, and review of weak topics.

## Features

- **20-Day Study Plan** - Structured curriculum covering all B1 grammar and exam skills
- **Progress Tracking** - Track completed days, current day, and overall progress
- **Review System** - Bot notes topics you struggle with and helps you review them later
- **Speaking Practice** - Send voice messages for speaking exercises, get feedback
- **Voice Responses** - Receive lessons as voice messages (optional)
- **Fun Roleplays** - Practice with immersive scenarios (apartment hunting, job interviews, etc.)

## The 20-Day Plan

**Week 1: Foundation**
- Days 1-2: Nebensätze (weil, dass, wenn, ob)
- Days 3-4: Perfekt (regular + irregular verbs)
- Day 5: Review + Dativ prepositions

**Week 2: Expressing Yourself**
- Days 6-7: Konjunktiv II (würde, hätte, wäre, könnte)
- Day 8: Expressing opinions
- Day 9: Komparativ und Superlativ
- Day 10: Relativsätze

**Week 3: Complex Structures**
- Day 11: obwohl und trotzdem
- Day 12: um...zu und damit
- Day 13: Adjektivdeklination
- Day 14: Präteritum
- Day 15: Review + Indirekte Fragen

**Week 4: Exam Skills**
- Day 16: Schreiben Teil 1 (informal email)
- Day 17: Schreiben Teil 2 (opinion text)
- Day 18: Schreiben Teil 3 + Sprechen Teil 1
- Day 19: Sprechen Teil 2 (presentation)
- Day 20: Full exam simulation

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Copy `.env.example` to `.env` and add your keys:
```
TELEGRAM_BOT_TOKEN=     # From @BotFather
GOOGLE_API_KEY=         # From Google AI Studio
ELEVENLABS_API_KEY=     # From ElevenLabs
POSTGRES_URL=postgresql://user:pass@localhost:5432/hanz
```

3. Run migrations:
```bash
uv run python migrate.py          # Run pending migrations
uv run python migrate.py status   # Check migration status
uv run python migrate.py reset    # Reset database (deletes all data!)
```

4. Run the bot:
```bash
uv run python bot.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and current progress |
| `/day` | Start today's lesson |
| `/day N` | Jump to day N (e.g., `/day 5`) |
| `/progress` | Show full progress overview |
| `/review` | Review topics you struggled with |
| `/done` | Mark current day as completed |
| `/roleplay` | Fun roleplay practice |
| `/voice on/off` | Toggle voice responses |

## How It Works

1. **Start a day** with `/day` - Hanz explains the grammar, then guides you through exercises
2. **Do exercises** - Answer in text, Hanz corrects and explains mistakes
3. **Speaking practice** - Send voice messages for speaking exercises
4. **Struggling?** - Hanz automatically notes weak topics for later review
5. **Finish** with `/done` - Marks day complete, moves to next day
6. **Review** with `/review` - Practice topics you found difficult

## Project Structure

```
hanz/
├── bot.py           # Telegram handlers
├── agent.py         # LangChain agent
├── config.py        # Environment config
├── database.py      # PostgreSQL database functions
├── migrate.py       # Database migration tool
├── study_plan.py    # 20-day curriculum content
├── prompts.py       # System prompts
├── plan.md          # Full study plan reference
├── migrations/      # SQL migration files
│   └── 001_initial.sql
└── tools/
    ├── study.py     # Study tracking tools
    └── voice.py     # ElevenLabs TTS, Gemini STT
```

## Tech Stack

- **python-telegram-bot** - Telegram integration
- **LangChain + LangGraph** - Agent with tools
- **Google Gemini** - LLM + voice transcription
- **ElevenLabs** - Text-to-speech
- **PostgreSQL** - Progress, vocabulary, grammar tracking
- **asyncpg** - Async PostgreSQL driver
