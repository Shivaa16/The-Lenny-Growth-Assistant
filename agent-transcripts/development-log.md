# Sanitized AI-Assisted Development Log

This is a curated record of material agent-assisted decisions, failures, corrections, and verification. Personal filesystem paths, environment values, credentials, and unrelated conversation have been removed. The implementation was directed and reviewed milestone by milestone; generated changes were not accepted without relevant tests or builds.

## Foundation and product framing

- Converted the ambiguous brief into a PRD, design principles, architecture boundaries, and seven milestones.
- Selected a low-storage profile: host Ollama with the 398 MB `qwen2.5:0.5b` chat model, `nomic-embed-text`, and PostgreSQL/pgvector.
- Chose explicit provider, retrieval, session, and artifact boundaries to make the system testable and replaceable.

## Failure: greeting requests failed

**Observed:** Sending only `Hi` attempted the normal retrieval/model path and surfaced a generic failure when infrastructure was unavailable.

**Correction:** Added a deterministic greeting route before embedding or generation. Added a test proving greetings call neither retrieval nor the model and still persist a complete turn.

## Retrieval and grounding decisions

- Used deterministic word-window chunking with overlap and SHA-256 source checksums.
- Combined vector similarity and PostgreSQL full-text scoring while retaining exact episode metadata.
- Added a threshold guard so empty/weak evidence never reaches generation.
- Marked transcript passages as untrusted data in system prompts to limit prompt-injection risk.

## Failure: stale UI preview

**Observed:** A theme change compiled but the visible preview appeared unchanged.

**Correction:** Diagnosed that no current preview server was attached, started the correct Vite process, and verified computed browser styles. This led to live-browser verification for later UI changes.

## Visual-direction correction

**Observed:** An early dark green/copper theme looked overly stylized and “AI generated.”

**Correction:** Replaced gradients, glow, texture, and mixed accents with a professional white/slate canvas, navy navigation, and one blue interaction color. Updated the design rationale and verified desktop artifact controls live.

## Artifact security and skill boundary

- Implemented persisted Markdown and HTML artifact contracts.
- Rendered Markdown as inert text and sanitized HTML with a conservative allowlist.
- Added an iframe with no sandbox permissions and a restrictive CSP.
- Encoded the linked Ship 30 guide’s specificity, credibility, 4A, and proven-structure principles into the dedicated service.
- Added tests showing executable HTML is removed and the model is not called without evidence.

## Failure: quality and environment assumptions

**Observed:** Initial artifact changes triggered line-length lint failures. A validation command also assumed the wrong working directory. Docker was unavailable in the development execution environment.

**Correction:** Fixed formatting, reran the complete suite, made paths explicit, and later installed and exercised the full Compose/Ollama stack on the target machine.

## Failures found during final live proof

**Observed:** Containerized ingestion failed because the slim API image had no Git executable. After ingestion, retrieval failed because the SQL chunk identifier was returned as `id` instead of the response contract's `chunk_id`. A weak relevance threshold also admitted an unrelated query, and unbounded local generation exceeded the artifact timeout.

**Correction:** Made repository commit metadata optional when Git is absent, explicitly labeled the retrieval column, raised the grounding threshold from `0.35` to `0.45`, and bounded Ollama output to 1,600 tokens with a 180-second timeout. Regression tests cover both code defects. The repeated live run indexed 25 transcripts into 2,041 chunks, returned grounded citations and a contextual follow-up, refused unrelated evidence, and produced a 1,383-word artifact with eight citations.

## Verification discipline

- Backend: unit/API tests for health, sessions, persistence rules, retrieval, provider contracts, grounding, artifacts, and sanitization.
- Frontend: TypeScript compilation, production Vite builds, and targeted live-browser state checks.
- Operations: offline Alembic migration generation, PowerShell smoke-script parsing, Compose dependency-graph checks, and GitHub Actions.
- Git: focused conventional commits, README updates alongside behavior changes, diff checks, and clean-worktree audits.
