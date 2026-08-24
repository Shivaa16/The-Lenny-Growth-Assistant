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

