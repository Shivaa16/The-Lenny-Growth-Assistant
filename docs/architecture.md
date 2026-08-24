# Architecture

## System boundaries

The browser communicates only with the FastAPI service. FastAPI owns validation, session orchestration, retrieval, provider selection, persistence, sanitization, and error normalization. PostgreSQL stores application records and vector embeddings. Ollama runs as a separate local service; Anthropic is an optional cloud provider.

## Planned components

- API layer: versioned HTTP contracts, validation, health endpoints, and structured errors
- Session service: session lifecycle and contextual message history
- Retrieval service: hybrid search, evidence selection, and citation construction
- Agent router: grounded answer, Ship 30 essay, and artifact-generation routes
- Provider adapters: consistent interface for Ollama and Anthropic
- Artifact service: typed Markdown/HTML payloads, sanitization, and persistence
- Ingestion worker: transcript parsing, chunking, embedding, refresh, and source traceability

## Initial API surface

- `GET /health/live`: process liveness
- `GET /health/ready`: dependency readiness
- `GET /api/v1/config`: evaluator-safe active-provider information
- `POST /api/v1/sessions`: create a session
- `GET /api/v1/sessions/{id}`: retrieve session and messages
- `POST /api/v1/sessions/{id}/messages`: send a message and stream/receive a response
- `GET /api/v1/artifacts/{id}`: retrieve a stored artifact

## Implemented persistence boundary

Conversation persistence follows a layered dependency flow:

`FastAPI router -> SessionService -> SessionRepository protocol -> SQLAlchemy repository -> PostgreSQL`

The service depends on a repository protocol rather than SQLAlchemy directly. This keeps product rules testable without a database and allows the persistence adapter to evolve independently. All write operations commit atomically and roll back before returning a normalized `persistence_unavailable` error.

## Data model

- `users`: lightweight evaluator metadata; authentication is out of scope
- `sessions`: ID, user ID, title, provider, model, created/updated timestamps
- `messages`: session ID, role, content, status, timestamps, model metadata
- `sources`: episode identity, title, guest, publication date, URL, transcript checksum
- `chunks`: source ID, ordinal, content, token count, embedding, metadata
- `citations`: message ID, chunk ID, quoted span, relevance score
- `artifacts`: session/message IDs, kind, title, content, sanitized content, timestamps

## Retrieval flow

1. Normalize the question with limited session context.
2. Produce an embedding using the configured embedding provider.
3. Execute vector similarity search and PostgreSQL full-text search.
4. Fuse and rerank candidates while preserving source diversity.
5. Apply a minimum evidence threshold.
6. Pass selected evidence to the agent as untrusted, citable context.
7. Validate structured citations against the selected chunk IDs.

### Ingestion and refresh

The transcript source is a shallow, locally cached checkout of the assignment-linked ChatPRD repository. Each `episodes/{guest}/transcript.md` file is parsed from YAML frontmatter, normalized, hashed, and split into deterministic overlapping word windows. Sources retain the repository-relative path, Git commit, and SHA-256 checksum so every answer can be traced to an exact indexed version.

Refresh is idempotent: unchanged checksums are skipped. A changed transcript is embedded first, then its source metadata and complete chunk set are replaced in one database transaction. Ollama or database outages fail fast rather than silently leaving a partially refreshed source.

### Hybrid retrieval

Every chunk has a 768-dimensional `nomic-embed-text` vector and a generated PostgreSQL English `tsvector`. Retrieval weights cosine similarity at 75% and capped keyword relevance at 25%, then applies the configured minimum score. The independent retrieval endpoint makes evidence selection observable and testable before answer generation is introduced.

## Security

- Secrets are loaded from environment variables and never returned to the browser.
- HTML is sanitized server-side with an allowlist.
- Scripts, event handlers, forms, external embeds, and dangerous URL schemes are removed.
- HTML renders in a sandboxed iframe without `allow-scripts` or `allow-same-origin`.
- A restrictive CSP is embedded into artifact documents.
- Database queries are parameterized through the ORM/query layer.
- Logs redact secrets and avoid recording full private prompts by default.

## Deployment topology

The evaluator profile uses Docker Compose for the API, web application, and PostgreSQL. Ollama can run on the host to use the laptop GPU. The low-storage developer profile runs web and API processes directly and connects to Supabase PostgreSQL.
