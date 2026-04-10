# AI Dungeon Master

Self-hosted AI-powered D&D 5e Dungeon Master with voice interaction, battle maps, and animated avatar.

## Quick Start

```bash
# Install dependencies
make install

# Start dev databases
make dev-up

# Run backend tests
make test-backend

# Run all tests
make test-all
```

## Architecture

- **Backend**: Python 3.12+ / FastAPI / SQLAlchemy / Pydantic
- **Frontend**: TypeScript / React / Vite
- **Databases**: PostgreSQL (game state) + MongoDB (SRD data) + Redis (cache)
- **LLM**: Provider-agnostic (Anthropic Claude, OpenAI, Ollama)

## Development

See `.env.example` for configuration options. Copy to `.env` and fill in your values.

Run `make help` for all available commands.
