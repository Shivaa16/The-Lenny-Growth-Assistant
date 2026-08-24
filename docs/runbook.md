# Evaluator Runbook

## Recommended demo path

1. Install Docker Desktop and Ollama, then start Ollama.
2. Pull the two local models:

   ```powershell
   ollama pull qwen2.5:3b
   ollama pull nomic-embed-text
   ```

3. Copy `.env.example` to `.env` and keep `LLM_PROVIDER=ollama`.
4. Start the application:

   ```powershell
   docker compose up --build -d
   docker compose ps
   powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
   ```

5. Prepare a fast transcript index from the host:

   ```powershell
   cd apps/api
   python -m pip install -e ".[dev]"
   python -m lenny_api.knowledge.sync
   python -m lenny_api.knowledge.cli --limit 25
   ```

6. Open `http://localhost:5173`, ask a focused product/growth question, inspect its sources, and generate a Ship 30 essay.

The API container reaches host Ollama through `host.docker.internal`. The indexing command runs on the host so the shallow transcript checkout remains outside Docker image layers and can be reused incrementally.

## Full-corpus preparation

Run the same ingestion command without `--limit`. Existing documents are checksum-skipped. The source checkout contains text and is comparatively small; embeddings stored in PostgreSQL are the material variable. Keep at least several gigabytes free for Docker images, models, database data, build cache, and operational headroom.

## Operational checks

| Check | Command | Healthy result |
| --- | --- | --- |
| Containers | `docker compose ps` | postgres, api, and web are healthy |
| Public readiness | `Invoke-RestMethod http://localhost:5173/health/ready` | `status: ok` |
| Provider | `Invoke-RestMethod http://localhost:5173/api/v1/config` | expected provider and model |
| Ollama | `Invoke-RestMethod http://localhost:11434/api/tags` | installed models |
| Smoke flow | `powershell -File scripts/smoke.ps1` | `Smoke test passed` |

## Troubleshooting

### `docker` is not recognized

Install and start Docker Desktop, then open a fresh terminal. Docker was not available in the development execution environment, so Compose is statically validated in CI/local checks but must be smoke-tested on a Docker-enabled machine before the recorded demo.

### API remains unhealthy

Run `docker compose logs api postgres`. The API applies Alembic migrations before Uvicorn starts; a malformed database URL or unavailable PostgreSQL will therefore fail visibly instead of serving a partially initialized application.

### Ollama provider is unavailable

Confirm Ollama is running on the host and both models appear in `/api/tags`. On Linux engines, Compose explicitly maps `host.docker.internal` to the host gateway. Do not change the container URL to `localhost`, which would point back to the API container.

### Port already allocated

Stop the conflicting process or change the host side of the mappings in `compose.yaml`. The defaults are `5173` for the product, `8000` for direct API access, and `5432` for PostgreSQL.

### Indexing is slow

Start with `--limit 25`. Ingestion is incremental, so it is safe to interrupt between completed transcripts and resume later. Ollama embedding batches are intentionally bounded to limit memory pressure.

### Resetting local infrastructure

`docker compose down` preserves the PostgreSQL volume. `docker compose down -v` deletes all locally indexed transcripts, sessions, messages, citations, and artifacts; use it only when a destructive reset is intentional.
