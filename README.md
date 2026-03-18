# Jarvis — Autonomous AI Assistant

> Your personal AI that actually does things. Jarvis understands your request, finds the best options, calls businesses on your behalf, and books appointments — all from a single command.

![Jarvis Dashboard](https://via.placeholder.com/1200x600/0A0A0F/6C63FF?text=Jarvis+Dashboard)

---

## What Jarvis Can Do

- **AI Planning** — Breaks down your request into a step-by-step execution plan using GPT-4o-mini
- **Real Location Search** — Finds actual businesses near you using Google Maps in real time
- **Voice Calling** — Calls businesses on your behalf and holds a natural two-way conversation
- **Calendar Aware** — Checks your real Google Calendar before booking anything
- **Memory** — Remembers your name, location, and preferences between sessions
- **Task History** — Every task is saved to a database so you can review what Jarvis did

### Example

```
You: "Book me a haircut tomorrow afternoon"

Jarvis:
  ✓ Found 52 Barbershop nearby ⭐ 4.6
  ✓ Checked calendar — free tomorrow afternoon
  ✓ Called salon and negotiated a 2pm slot
  ✓ Added to Google Calendar
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 |
| AI Planning | OpenAI GPT-4o-mini |
| Voice AI | OpenAI GPT-4o-mini + ElevenLabs |
| Location Search | Google Maps Places API |
| Calendar | Google Calendar API |
| Voice Calls | Twilio + ElevenLabs |
| Database | PostgreSQL + SQLAlchemy async |
| Task Queue | ARQ (Redis-backed) |
| Tunnel | ngrok |
| Frontend | React + Vite + Tailwind CSS |
| Auth | JWT + Google OAuth |
| Containerization | Docker Compose |

---

## Project Structure

```
jarvis-agent/
├── app/
│   ├── agents/
│   │   ├── executor.py        # Executes multi-step plans
│   │   ├── memory.py          # User preferences (PostgreSQL)
│   │   ├── planner.py         # Converts requests into plans
│   │   └── prompts.py         # System prompts
│   ├── api/
│   │   ├── auth.py            # JWT + Google OAuth
│   │   ├── routes.py          # /command, /tasks, /memory
│   │   └── voice.py           # Twilio webhooks, voice conversation
│   ├── core/
│   │   └── config.py          # Settings from environment
│   ├── models/
│   │   └── task.py            # Task, UserMemory, User models
│   ├── services/
│   │   ├── auth_service.py    # bcrypt + JWT
│   │   └── llm_service.py     # OpenAI plan generation
│   ├── tools/
│   │   ├── calendar_tool.py   # Google Calendar integration
│   │   ├── calling.py         # Twilio outbound calls
│   │   └── search_tool.py     # Google Maps search
│   ├── workers/
│   │   └── agent_worker.py    # ARQ background worker
│   └── main.py                # FastAPI app entry point
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── HomePage.jsx
│       │   ├── AuthPage.jsx
│       │   ├── OnboardingPage.jsx
│       │   └── Dashboard.jsx
│       └── components/
│           ├── CommandInput.jsx
│           ├── TaskCard.jsx
│           ├── VoicePanel.jsx
│           └── TaskHistory.jsx
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Prerequisites

- Docker Desktop
- ngrok account (free) — [dashboard.ngrok.com](https://dashboard.ngrok.com)
- OpenAI API key — [platform.openai.com](https://platform.openai.com)
- Google Cloud project with Maps + Calendar APIs enabled
- Twilio account (for real phone calls)
- ElevenLabs account (for AI voice)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Parsa-Meshkini/Jarvis.git
cd Jarvis
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Fill in all values:

```env
# App
APP_NAME=Jarvis
DEBUG=false

# AI
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql+asyncpg://jarvis:jarvis@postgres:5432/jarvis
REDIS_URL=redis://redis:6379

# Google Maps
GOOGLE_MAPS_API_KEY=AIza...

# Google Calendar (service account JSON, single line)
GOOGLE_CALENDAR_CREDENTIALS={"type":"service_account",...}
GOOGLE_CALENDAR_ID=your-calendar-id@gmail.com

# Google OAuth (for Google Sign-In)
GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...
GOOGLE_REDIRECT_URI=https://your-ngrok-url.ngrok-free.app/auth/google/callback
FRONTEND_URL=http://localhost:3000

# Twilio (for voice calls)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
YOUR_PHONE_NUMBER=+1...

# ElevenLabs (for AI voice)
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=cjVigY5qzO86Huf0OWal

# ngrok
NGROK_AUTHTOKEN=...
NGROK_URL=https://your-ngrok-url.ngrok-free.app

# Auth
SECRET_KEY=your-random-secret-key
```

### 3. Start everything

```bash
docker compose up --build -d
```

This starts: PostgreSQL, Redis, API, Worker, Frontend, and ngrok.

### 4. Update Twilio webhook

After Docker starts, run this to automatically point Twilio at your current ngrok URL:

```bash
python3 scripts/update_twilio_webhook.py
```

### 5. Open the app

Visit [http://localhost:3000](http://localhost:3000)

---

## Running Locally (without Docker)

```bash
# Terminal 1 — API
python run.py

# Terminal 2 — Background worker
PYTHONPATH=. arq app.workers.agent_worker.WorkerSettings

# Terminal 3 — Frontend
cd frontend && npm run dev

# Terminal 4 — ngrok
ngrok http 8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/command` | Submit a task to Jarvis |
| GET | `/tasks` | List recent tasks |
| GET | `/tasks/{id}` | Get task details |
| POST | `/memory` | Save a user preference |
| GET | `/memory` | Get all preferences |
| DELETE | `/memory/{key}` | Delete a preference |
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Sign in |
| GET | `/auth/google` | Google OAuth sign-in |
| GET | `/voice/active` | List active voice calls |
| GET | `/voice/status/{sid}` | Get call transcript |

---

## How It Works

```
User Command
     │
     ▼
  Planner (GPT-4o-mini)
  Generates JSON execution plan
     │
     ▼
  Executor
  Runs each step in sequence
     │
  ┌──┴──────────────────────────┐
  │                             │
  ▼                             ▼
search_places              check_calendar
Google Maps API            Google Calendar API
  │                             │
  ▼                             ▼
call_business              add_to_calendar
Twilio outbound call       Creates calendar event
ElevenLabs voice           
```

### Booking Flow

1. **Search** — Finds businesses near the user using Google Maps
2. **Calendar check** — Verifies the user is free at the requested time
3. **Call** — Jarvis calls the business using Twilio, speaks using ElevenLabs, listens with Twilio STT, thinks with OpenAI
4. **Calendar add** — Adds the confirmed booking to Google Calendar

---

## Voice System

When Jarvis makes a call:

- **Outbound**: Twilio dials the business
- **Speech synthesis**: ElevenLabs generates natural-sounding voice
- **Speech recognition**: Twilio STT transcribes what the business says
- **AI response**: OpenAI decides what to say next
- **Webhook**: `/voice/booking-respond` handles each turn of the conversation

The live conversation transcript appears in the Voice tab of the dashboard in real time.

---

## Dashboard Features

- **Command bar** — Type any request in natural language
- **Task tab** — See the full execution plan and results with step-by-step breakdown
- **Voice tab** — Live transcript of active phone calls
- **Memory tab** — View and edit saved preferences (name, location, preferred time)
- **History sidebar** — Browse all past tasks

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | Powers all AI planning and voice conversation |
| `GOOGLE_MAPS_API_KEY` | ✅ | Business search |
| `GOOGLE_CALENDAR_CREDENTIALS` | Optional | Real calendar integration (JSON) |
| `TWILIO_ACCOUNT_SID` | Optional | Real phone calls |
| `TWILIO_AUTH_TOKEN` | Optional | Twilio auth |
| `ELEVENLABS_API_KEY` | Optional | AI voice (falls back to Polly) |
| `NGROK_AUTHTOKEN` | ✅ | Public webhook URL for Twilio |
| `GOOGLE_CLIENT_ID` | Optional | Google Sign-In |
| `GOOGLE_CLIENT_SECRET` | Optional | Google Sign-In |

Without Twilio credentials, call steps are simulated. Without ElevenLabs, Twilio's Polly neural voice is used.

---

## Built With

- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAI](https://platform.openai.com/)
- [Twilio](https://www.twilio.com/)
- [ElevenLabs](https://elevenlabs.io/)
- [Google Maps Platform](https://developers.google.com/maps)
- [Google Calendar API](https://developers.google.com/calendar)
- [React](https://react.dev/) + [Vite](https://vitejs.dev/) + [Tailwind CSS](https://tailwindcss.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)
- [Docker](https://www.docker.com/)
- [ngrok](https://ngrok.com/)

---

## License

MIT
