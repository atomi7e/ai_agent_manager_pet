# AI Planner Bot

A Telegram bot that turns a task into a short step-by-step checklist with Google Gemini. You can describe the task in
text, send a photo with a caption, or record a voice message. A Telegram Mini App shows the same tasks next to an XP
chart, a title shop, a leaderboard and a focus timer.

Pet project, February 2026. The bot's interface is in Russian.

> **Status: prototype.** Planning from text, photos and voice works end to end. Profiles, XP, achievements and
> long-term memory are stubbed out in this version, see [Known limitations](#known-limitations).

## What it does

| Feature | How it works |
|---|---|
| Plan from text | The message goes to Gemini with a planning prompt and comes back as 3–6 steps |
| Plan from a photo | The photo and its caption are sent to Gemini in one request |
| Plan from a voice message | The OGG voice note is sent to Gemini as audio, without a separate speech-to-text step |
| Checklist | Each step becomes an inline button you can tick; a task is accepted only when every step is ticked |
| Quiz | Gemini writes a multiple-choice question on a random topic |
| Focus and reminders | A 25-minute Pomodoro button and `/remind 10m text`, both on the bot's job queue |
| Rewards | Finishing a task or answering the quiz is meant to give XP and coins that buy titles (not saved yet) |
| Mini App | A FastAPI page inside Telegram: task list, new task with an AI plan, 7-day XP chart, shop, leaderboard, timer |

## How it works

```
Telegram chat ──► src/main.py (python-telegram-bot, polling)
                     └─ src/bot/handlers.py ──► src/services/ai_service.py ──► Gemini (gemini-flash-latest)
                                             └─► src/database.py ──► planner.db (SQLite)

Mini App      ──► src/api.py (FastAPI + Jinja) ──► same AI service and database
```

- Each user gets their own Gemini chat session, so follow-up messages keep context. Sessions live in memory and
  reset when the bot restarts.
- Before planning, a second Gemini call looks for lasting facts about the user in the message ("I study Python"),
  meant to be fed into later prompts.
- `docker-compose.yml` runs the bot and the web app as two services that share one `planner.db`.

## Run it

You need Python 3.11, a bot token from [@BotFather](https://t.me/BotFather) and a Gemini API key from
[Google AI Studio](https://aistudio.google.com/apikey).

```bash
git clone https://github.com/atomi7e/ai_agent_manager_pet.git
cd ai_agent_manager_pet
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then put your own keys into .env
```

Start the bot:

```bash
python -m src.main
```

Start the Mini App:

```bash
python -m uvicorn src.api:app --port 8000
```

Telegram opens Mini Apps only over HTTPS, so expose port 8000 through a tunnel such as `ngrok http 8000` and put that
URL into `NGROK_URL` in `src/bot/handlers.py`.

With Docker, create an empty database file first, otherwise Docker mounts a folder in its place:

```bash
touch planner.db
docker compose up --build
```

`check_models.py` lists the Gemini models your key can use. It needs `pip install python-dotenv`.

## Project layout

| Path | What is inside |
|---|---|
| `src/main.py` | Bot entry point and handler registration |
| `src/bot/handlers.py` | Commands, keyboard buttons, checklist callbacks, timers |
| `src/services/ai_service.py` | Gemini calls: plans, fact extraction, quiz |
| `src/api.py` | FastAPI app and JSON endpoints for the Mini App |
| `src/database.py` | SQLite schema and queries |
| `src/templates/index.html` | Mini App interface (Telegram Web App JS, Chart.js) |
| `src/config.py` | Reads the keys from `.env` |

## Known limitations

- **Stubbed storage.** `update_user_meta`, `save_fact`, `get_user_facts`, `clear_memory` and
  `check_achievements_unlock` in `src/database.py` are placeholders. Users are never written to the `users` table, so
  XP, coins, levels, the leaderboard, achievements and remembered facts are not saved. Plans themselves are saved.
- **No authentication in the Mini App API.** Endpoints take `user_id` from the query string and do not validate
  Telegram `initData`, so anyone who has the URL can act as any user.
- **Hard-coded Mini App URL** in `src/bot/handlers.py`.
- **`.env` ends up in the Docker image.** There is no `.dockerignore`, so `COPY . .` copies it in.
- **Role switch is not wired.** The role buttons only acknowledge the click; the role is not stored.
- **Deprecated SDK.** The bot uses `google-generativeai`, which Google has replaced with `google-genai`.
- **No tests.**

## Stack

Python 3.11 · python-telegram-bot (job queue) · Google Gemini · FastAPI · Jinja2 · aiosqlite · Pillow ·
Docker Compose · Telegram Web App JS · Chart.js
