# AI Dungeon Master

Self-hosted AI-powered D&D 5e Dungeon Master with voice interaction, battle maps, and animated avatar.

## Features

- 🎲 **Complete D&D 5e Rules Engine** — Dice rolling, combat, spells, conditions, ability checks, death saves
- 🤖 **AI Narration** — Provider-agnostic LLM (Anthropic Claude, OpenAI, Ollama) generates narrative
- 🗣️ **Voice I/O** — Speech-to-text (Whisper) + Text-to-speech (Piper/Coqui XTTS)
- 🗺️ **Battle Maps** — Grid-based maps with tokens, terrain, and fog of war
- 📷 **Board Vision** — Camera capture + AI analysis of physical game boards
- 🎭 **DM Avatar** — Animated face with expression mapping and lip sync
- 📚 **SRD Reference** — Built-in D&D 5e spells, monsters, equipment, classes, races
- 🤝 **Player Trading & Inventory** — Item/gold trades with counter-offers, DM arbitration veto, and in-character `use`/`equip` actions
- 🐳 **Docker Ready** — Production compose with GPU overlay for homelab deployment

## Quick Start

```bash
# Install dependencies
make install

# Run backend (terminal 1)
cd backend && uvicorn app.main:create_app --factory --reload

# Run frontend (terminal 2)
cd frontend && npm run dev

# Open http://localhost:5173
```

## Testing (951 tests)

```bash
make test-backend        # 772 pytest tests
make test-frontend       # 100 Vitest tests
make test-e2e            # 79 Playwright tests
make test-all            # Backend + Frontend
```

## Production Deployment (Docker)

```bash
cp .env.example .env     # Configure your settings
make docker-up           # Start full stack
make docker-gpu          # With GPU (Ollama + voice)
```

## Architecture

- **Backend**: Python 3.12 / FastAPI / SQLAlchemy 2.0 / Pydantic
- **Frontend**: TypeScript / React 19 / Vite / React Router
- **Database**: PostgreSQL + Alembic migrations (SQLite for dev)
- **LLM**: Anthropic Claude / OpenAI / Ollama (provider-agnostic)
- **Voice**: Whisper STT / Piper TTS (CPU) / Coqui XTTS (GPU)
- **Real-time**: WebSocket for game events, map sync, audio streaming

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `/api/auth/*` | Register, login, token auth |
| `/api/campaigns/*` | Campaign CRUD |
| `/api/characters/*` | Character CRUD + `POST /{id}/gold` for adjustments |
| `/api/items/*` | `use`, `equip`, `unequip` (in-character item actions) |
| `/api/game/*` | Game session management |
| `/api/game/sessions/{id}/trades/*` | Player trades: create / respond / counter / veto (DM) |
| `/api/maps/*` | Map state + token movement |
| `/api/avatar/*` | Avatar expression + speaking |
| `/api/vision/*` | Board capture + analysis |
| `/api/srd/*` | D&D 5e reference data |
| `WS /ws/game/{id}` | Game events + chat |
| `WS /ws/audio/{id}` | Voice streaming |

## Development

See `.env.example` for configuration. Run `make help` for all commands.

## Multi-agent simulation (test the app without humans)

A standalone Python harness in `scripts/simulate/` drives the real backend
with N bot players over the actual WebSocket protocol. Use it to iterate on
gameplay without wrangling humans:

```bash
# 1. Boot the backend (any mode — mock narration works for CI).
make dev-up && uvicorn app.main:app --port 8000  # or `docker compose up backend`

# 2. Install harness deps (isolated from backend prod deps).
make simulate-deps

# 3. Headless 3-bot smoke (no LLM, no GPU — runs in ~10s, deterministic).
make simulate-smoke

# 4. 4-persona free-roleplay tavern brawl (uses Ollama if reachable, else
#    falls back to scripted bots).
SIMULATE_OLLAMA_HOST=http://192.168.1.94:11434 make simulate-tavern
```

Per-run output is written to `runs/<scenario>-<timestamp>/`:
`transcript.jsonl` (every WS frame), `summary.json`, and
`assertion_failures.json` if any.

See `scripts/simulate/scenarios/` for the scenario format and
`scripts/simulate/agents.py` for persona definitions.
