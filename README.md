# Lenny Growth Assistant

An AI-powered research and writing assistant grounded in transcripts from Lenny's Podcast. The product supports persistent chat sessions, source-backed answers, a dedicated Ship 30 for 30 writing skill, and safe in-app Markdown/HTML artifacts.

## Project status

Milestone 1 establishes the product brief and application foundation. Transcript ingestion, retrieval, agent routing, persistence, and the complete interface will be added incrementally.

## Architecture

- `apps/api`: FastAPI application and provider configuration
- `apps/web`: React and TypeScript frontend
- `docs`: product, design, and architecture decisions
- `infra`: local infrastructure configuration
- `agent-transcripts`: sanitized AI-assisted development logs

## Low-storage development profile

- Ollama with `qwen2.5:3b`
- Ollama `nomic-embed-text` embeddings
- Supabase PostgreSQL with pgvector for normal development
- Local FastAPI and React processes
- Docker Compose retained as the evaluator's reproducible startup path

## Prerequisites

- Python 3.11+
- Node.js 20+
- Ollama
- A PostgreSQL database (Supabase is supported)

## Run the persistent conversation milestone

1. Copy `.env.example` to `.env` and set `DATABASE_URL` to a PostgreSQL connection string.
2. Install the API and run the migration:

   ```powershell
   cd apps/api
   python -m pip install -e ".[dev]"
   alembic upgrade head
   uvicorn lenny_api.main:app --reload
   ```

3. In a second terminal, start the web application:

   ```powershell
   cd apps/web
   pnpm install
   pnpm run dev
   ```

The evaluator path is `docker compose up --build`. It starts PostgreSQL, applies migrations, and serves the API and web application. Ollama stays on the host so it can use the laptop GPU.

## Build the transcript index

The source is the assignment-linked [ChatPRD transcript archive](https://github.com/ChatPRD/lennys-podcast-transcripts). The sync command creates a shallow checkout and refuses to overwrite a directory with a different Git origin.

```powershell
cd apps/api
python -m lenny_api.knowledge.sync
python -m lenny_api.knowledge.cli
```

Ingestion is incremental. Each source stores its repository path, repository commit, and SHA-256 content checksum. Unchanged transcripts are skipped; changed transcripts replace their chunks atomically. The default chunk profile is 220 words with 40 words of overlap, embedded using `nomic-embed-text` through Ollama.

Retrieval can be inspected independently from generation through `POST /api/v1/retrieval/search`. It combines pgvector cosine similarity with PostgreSQL full-text ranking, returns episode metadata with every passage, and reports an empty evidence list when the configured grounding threshold is not met.

## Conversational providers

`LLM_PROVIDER` selects the generation adapter without application-code changes:

- `ollama` uses the local `/api/chat` endpoint and defaults to `qwen2.5:3b`.
- `anthropic` uses the required Claude Agent SDK with tools disabled, one bounded turn, a timeout, and a configurable per-request budget.

Both providers receive the same constrained evidence prompt and recent persisted session context. Retrieval runs before generation; when no passage clears the grounding threshold, the system returns a deterministic insufficient-evidence response without calling a model. Greetings are routed locally without retrieval so the interface remains natural and inexpensive.

Each successful turn atomically stores the user message, assistant answer, provider/model usage metadata, and the exact chunk citations presented in the UI.

### Ship 30 artifact flow

Enter a focused topic (or ask a grounded question first), then choose **Ship 30 essay** in the composer. The dedicated skill retrieves up to eight transcript passages, asks the active provider for an approximately 1,250-word structured essay, persists the artifact and source manifest, and opens it in the responsive artifact pane.

- Markdown is displayed as inert text rather than injected into the application DOM.
- HTML artifacts pass through a server-side allowlist sanitizer and render in a sandboxed iframe.
- The iframe embeds a restrictive Content Security Policy and receives no script, navigation, or same-origin capability.
- When retrieval has no supporting evidence, the model is not called and the artifact explains how to narrow the topic.

Artifact endpoints:

- `POST /api/v1/sessions/{session_id}/artifacts`
- `GET /api/v1/sessions/{session_id}/artifacts`
- `GET /api/v1/artifacts/{artifact_id}`

## Quality gates

```powershell
cd apps/api
pytest
ruff check src tests migrations

cd ../web
pnpm run build
```
