# Copilot Instructions — DungeonMaster Project

## Project Overview

Self-hosted AI Dungeon Master for D&D 5e. Python/FastAPI backend + React/TypeScript frontend.
Deployed on Proxmox homelab (VM 102) with AMD RX 6650 XT GPU running Ollama via Vulkan.

## Architecture

- **Backend**: Python 3.12+ / FastAPI / Pydantic / in-memory storage
- **Frontend**: React 19 / TypeScript 6 / Vite 8 / React Router 7
- **LLM**: Provider-agnostic (Anthropic, OpenAI, Ollama adapters). Ollama runs natively on VM with `OLLAMA_VULKAN=1`
- **Testing**: pytest (backend), Vitest (frontend), Playwright (E2E)
- **Deployment**: Docker Compose on VM 102 (`dungeon@192.168.1.94`)

### Key Design Principle

The **rules engine is deterministic code** — never LLM. The LLM only narrates; it receives structured state snapshots and produces narrative text. This prevents hallucinated math.

## Critical Workflow Rules

### 1. Never loop on reading — act on results immediately

When a background agent or shell command completes, read the results **once**, then immediately proceed to integrate the changes. Do NOT repeatedly call `read_agent`, `read_powershell`, or `view` on the same resources. If you have the data, make the edits.

### 2. Show progress after every action

After completing each discrete unit of work (a file edit, a test run, a fix), briefly tell the user what was done. Never go more than 2-3 tool calls without communicating progress.

### 3. Restart stale servers after backend changes

After modifying backend code, always restart the running server/containers. The deployed stack uses Docker Compose — run `docker compose restart backend` on the VM or restart the local dev server. Stale processes cause phantom bugs (e.g., the `current_scene` field required error).

### 4. Finish what you start

If a background task completes (portrait generation, bug fix, etc.), integrate its results before moving to the next task. Never leave completed work unintegrated.

### 5. UI quality bar is high

The user expects a polished, dark-fantasy themed UI — not basic/default styling. When building UI:
- Use the established CSS variable system (`--gold`, `--gold-light`, `--gold-dim`, `--gold-bg`, `--gold-border`)
- **`--gold-dark` does NOT exist** — use `--gold-dim` instead
- Fonts: Cinzel (headings), Crimson Text (body)
- Dark backgrounds with gold accents, parchment textures
- Test with Playwright visual screenshots for each iteration

## Testing Commands

```bash
# Backend tests
cd backend && python -m pytest -x -q

# Frontend unit tests
cd frontend && npx vitest run --reporter=verbose

# Playwright E2E tests
cd frontend && npx playwright test

# Full suite
make test-all
```

## Frontend Conventions

### API Route Mocks (Playwright)

These URLs must match exactly in test mocks:
- Characters: `/api/characters?campaign_id={id}` (NOT `/api/campaigns/{id}/characters`)
- Game session state: `/api/game/sessions/{id}/state` (note: `sessions` plural)
- Use `waitForSelector` after navigation, not just `waitForLoadState('networkidle')` — React needs time to render after data loads

### CSS Architecture

- `index.css`: Global theme variables, reset, typography, scrollbar
- `App.css`: All component/page styles (~1450+ lines)
- `GameSession.css`: Game session layout (~780+ lines)

### Pre-made Characters

`frontend/src/data/premadeCharacters.ts` contains 10 pre-made characters with `CLASS_COLORS`, `RACE_SYMBOLS`, and portrait paths at `/portraits/{name}.jpg`.

## Deployment

### VM Access
- SSH: `dungeon@192.168.1.94`
- Proxmox: node `stewart`, VM 102 (Ubuntu 24.04, 8 cores, 8GB RAM)
- GPU: RX 6650 XT via PCI passthrough, Vulkan (not ROCm — ROCm fails in VM)

### Docker Stack
```bash
ssh dungeon@192.168.1.94
cd DungeonMaster
docker compose up -d
docker compose logs -f backend  # check health
```

### Ollama (Native, not Docker)
- Runs as systemd service with `OLLAMA_VULKAN=1` override
- Model: `llama3.1:8b` (~46.5 tok/s on GPU)
- Backend connects via `OLLAMA_BASE_URL=http://host.docker.internal:11434`

## Git Conventions

- Always include: `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`
- Run tests before committing
- Descriptive commit messages summarizing what changed and test counts
