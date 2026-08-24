# Evaluation and Submission Checklist

This matrix maps the take-home brief to concrete implementation evidence. It is intended to let an evaluator inspect the solution quickly and to prevent the submission from relying on unsupported claims.

## Requirement coverage

| Brief requirement | Implementation evidence | Verification |
| --- | --- | --- |
| FastAPI contracts and health | Versioned routers, Pydantic validation, structured error envelope, `/health/live`, `/health/ready` | API test suite and smoke script |
| Independent persistent sessions | PostgreSQL sessions/messages, bounded history, session-scoped repositories | Session service/API tests |
| Claude Agent SDK | Bounded Anthropic adapter with tools disabled, timeout, and cost budget | Provider contract test |
| Mandatory local model | Ollama chat and embedding adapters; provider visible in UI | Provider contract tests; final demo must show `/api/v1/config` |
| Model toggle | `LLM_PROVIDER`, model variables, provider-neutral interface | Configuration endpoint and unit tests |
| Transcript knowledge base | Shallow source sync, deterministic parser/chunker, checksums, pgvector + full-text retrieval | Knowledge and retrieval tests |
| Grounded conversation | Evidence-only prompt, inline citations, follow-up context, deterministic refusal | Agent routing tests |
| Ship 30 skill | Dedicated service encoding specificity, curator credibility, 4A lens, and consistent proven structure | Artifact skill test and source metadata |
| Markdown and HTML artifacts | Typed persisted artifacts with both composer actions | Production build and manual UI plan |
| Safe artifact viewer | Inert Markdown; HTML allowlist sanitizer; empty-sandbox iframe with CSP | Sanitizer tests and manual UI plan |
| Operable deployment | Compose readiness graph, migrations, health checks, low-storage indexing, smoke test | Static validation completed; live Docker smoke pending |
| Observability and resilience | Structured logs, normalized provider/embedding/database errors, timeouts, empty-evidence states | Error-path tests and runbook |
| Documentation/handoff | PRD, design, architecture, runbook, manual plan, demo script, agent log | Repository audit |

## Submission blockers

- [ ] Run `docker compose up --build -d` on a Docker-enabled machine.
- [ ] Run `scripts/smoke.ps1` against the containerized deployment.
- [ ] Index at least the 25-transcript demo subset with Ollama.
- [ ] Complete the manual UI plan in `docs/manual-test-plan.md`.
- [ ] Record the 2–3 minute camera-on demo using `docs/demo-script.md`.
- [ ] Upload the demo to YouTube and add its URL to the README.
- [ ] Confirm the GitHub repository is public and GitHub Actions is green.
- [ ] Submit the repository and video through the assignment form before the deadline.

These items are deliberately not pre-checked: they require the submitter's Docker runtime, camera, YouTube account, or GitHub settings.
