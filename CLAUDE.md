# Hanz - B1 German Exam Prep Bot

A Telegram bot that guides you through a structured 20-day B1 exam preparation plan. Features daily lessons with grammar, exercises, speaking practice, progress tracking, and review of weak topics.

## Features

- **20-Day Study Plan** - Structured curriculum covering all B1 grammar, vocabulary, and exam skills
- **Integrated Vocabulary** - Topic-based vocabulary (Reisen, Arbeit, Umwelt, Technologie, Gesundheit, Wohnen) built into each day
- **Progress Tracking** - Track completed days, current day, and overall progress
- **Review System** - Bot notes topics you struggle with and helps you review them later
- **Speaking Practice** - Send voice messages for speaking exercises, get feedback
- **Proactive Voice Messages** - Bot sends voice messages as exercises (dictation, listening comprehension, drills)
- **Writing Exercises** - Structured writing tasks with detailed feedback
- **Voice Responses** - Receive lessons as voice messages (optional)
- **Fun Roleplays** - Practice with immersive scenarios (apartment hunting, job interviews, etc.)

## The 20-Day Plan

**Week 1: Foundation + Reisen + Arbeit**
- Day 1: weil/dass + Reisen (Transportation & Booking)
- Day 2: wenn/ob + Reisen (At the Destination)
- Day 3: Review Nebensätze + Reisen (Problems & Solutions)
- Day 4: Perfekt (Regular) + Arbeit (Jobs & Workplace)
- Day 5: Perfekt (Irregular + sein) + Arbeit (Applications & Career)

**Week 2: Opinions & Self-Expression + Umwelt + Technologie**
- Day 6: Konjunktiv II (würde) + Arbeit (Work-Life) + Umwelt (Intro)
- Day 7: Konjunktiv II (hätte/wäre/könnte) + Umwelt (Problems)
- Day 8: Meinungsäußerung + Umwelt (Solutions & Debates)
- Day 9: Komparativ/Superlativ + Technologie (Devices & Internet)
- Day 10: Relativsätze (Basics) + Technologie (Social Media)

**Week 3: Complex Structures + Gesundheit + Wohnen**
- Day 11: Relativsätze (Advanced) + Technologie (Full) + Gesundheit (Intro)
- Day 12: obwohl/trotzdem + Gesundheit (Doctor & Treatment)
- Day 13: um...zu/damit + Gesundheit (Lifestyle & Prevention)
- Day 14: Adjektivdeklination + Wohnen (Types & Rooms)
- Day 15: Präteritum + Wohnen (Location & Neighborhood)

**Week 4: Exam Skills + Meinungsphrasen**
- Day 16: Indirekte Fragen + Meinungsphrasen
- Day 17: Schreiben Teil 1 (informal email)
- Day 18: Schreiben Teil 2 + Teil 3
- Day 19: Sprechen Teil 1 + Teil 2
- Day 20: Full review + exam simulation

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

1. **Start a day** with `/day` - Hanz explains the grammar, introduces vocabulary, then guides you through exercises
2. **Vocabulary refresh** - Quick review of previous days' vocabulary before new material
3. **Grammar exercises** - Fill-in-the-blank, transformations, sentence building
4. **Writing exercises** - Structured writing tasks (emails, stories, opinions) with detailed feedback
5. **Speaking practice** - Send voice messages for speaking exercises
6. **Voice exercises** - Hanz proactively sends voice messages for dictation, listening comprehension, and drills
7. **Struggling?** - Hanz automatically notes weak topics for later review
8. **Finish** with `/done` - Marks day complete, moves to next day
9. **Review** with `/review` - Practice topics you found difficult

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
