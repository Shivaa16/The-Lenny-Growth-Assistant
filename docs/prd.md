# Product Requirements Document

## 1. Discovery brief

### Primary user and problem

The primary user is a product manager, growth lead, founder, or operator who wants to apply lessons from Lenny's Podcast without manually searching hours of transcripts. They need defensible answers, reusable writing, and presentable artifacts, but should not need to understand prompting, retrieval systems, or model infrastructure.

### Job to be done

When I face a product or growth decision, help me find and synthesize the most relevant lessons from Lenny's Podcast, show me where the claims came from, and turn the result into an artifact I can use or share.

### Pain removed

- Searching individual episodes and transcripts manually
- Losing the provenance of advice after synthesis
- Rewriting research into a memo, essay, or HTML artifact
- Managing model selection and prompt mechanics

### Success metrics

Primary product metric: at least 80% of a curated evaluation set of answerable questions returns an answer with one or more relevant transcript citations and no unsupported material claims.

Primary operational metric: a fresh evaluator can clone, configure, and reach a healthy application in 10 minutes or less using the documented startup path.

Supporting measures:

- Median grounded-answer latency below 12 seconds with the local 3B model on the target laptop
- 100% of unsupported evaluation questions produce an explicit insufficient-evidence response
- 100% of generated HTML artifacts are rendered using the documented sanitization and isolation policy

## 2. Assumptions

- The evaluator values a complete, trustworthy workflow over broad transcript coverage.
- The demo machine has 16 GB RAM and an RTX 3050, so the default local model is `qwen2.5:3b`.
- A cloud-hosted PostgreSQL instance is acceptable for the low-storage development profile; Docker Compose provides a local evaluator alternative.
- Transcript repository licensing permits use for this evaluation. The system stores source metadata and transcript excerpts, not republished feeds.
- Cloud Claude is optional at runtime; the product remains demonstrable using Ollama.
- Markdown and HTML/CSS artifacts do not require JavaScript execution.

## 3. Scope

### Included

- Persistent, independent chat sessions
- Grounded answers with episode/source citations
- Follow-up questions using session context
- Explicit insufficient-evidence behavior
- Ollama and Anthropic provider configuration
- Ship 30 for 30 essay generation as a dedicated skill
- Markdown and HTML/CSS artifact generation
- Split chat and artifact-viewer experience
- Sanitized and sandboxed artifact rendering
- Structured logging, health checks, errors, and critical tests
- Reproducible evaluator setup and operational handoff

### Intentionally excluded from the first release

- User authentication and multi-tenant authorization
- Web browsing or knowledge outside the transcript collection
- Transcript editing and content-management UI
- JavaScript execution inside generated artifacts
- Collaborative editing and artifact version branches
- Fine-tuning a model

These exclusions keep the submission focused on grounding, operability, and a polished end-to-end workflow.

## 4. Core user flows

### Grounded research

1. User starts a new chat.
2. User asks a product or growth question.
3. System retrieves relevant transcript passages.
4. Agent produces an answer constrained to retrieved evidence.
5. UI displays citations that identify the episode and passage.
6. User asks a follow-up; the session retains relevant context.

### Ship 30 for 30 essay

1. User requests an essay from the current answer or topic.
2. Router invokes the explicit Ship 30 skill.
3. Skill creates an approximately 1,250-word grounded essay with hook, narrative progression, skimmable structure, and specific takeaway.
4. Result opens as a Markdown artifact beside the conversation.

### HTML artifact

1. User requests a shareable HTML/CSS artifact.
2. Agent returns a typed artifact payload rather than raw chat text.
3. Server sanitizes the payload and stores it with the session.
4. Viewer renders it in a sandboxed iframe with scripts disabled.

## 5. Acceptance criteria

- A new session receives a stable ID and cannot see another session's messages.
- Messages, session metadata, timestamps, citations, and artifacts persist in PostgreSQL.
- The active model provider is visible in the UI.
- Missing Ollama, missing cloud keys, timeouts, database failures, and empty retrieval produce actionable errors.
- Every grounded answer exposes its transcript sources.
- Unsupported questions do not receive invented answers.
- The local Ollama profile completes the primary demo flow.
- Markdown renders safely; HTML/CSS renders without scripts, top-level navigation, or same-origin access.
- Critical API, retrieval, routing, and persistence behavior has automated coverage.

## 6. Risks and trade-offs

- Hallucination: constrain synthesis to retrieved passages, require citations, and test unsupported questions.
- Local-model quality: use a narrow system contract, strong retrieval, structured outputs, and a visible optional Claude provider.
- Latency: retrieve a small evidence set, stream generation, and keep the local context budget bounded.
- Cost: local generation is the default; cloud usage is opt-in.
- Data leakage: do not send transcripts to cloud providers unless the evaluator explicitly selects cloud mode.
- Prompt injection in transcripts: label retrieved text as untrusted evidence and prohibit it from changing system behavior.
- Unsafe rendering: sanitize markup, disallow scripts and event handlers, and use a restrictive iframe sandbox and CSP.
- Scope pressure: prefer a reliable vertical slice and documented extension points over partially implemented features.

## 7. Implementation plan

1. Application foundation and health contracts
2. Database schema and session persistence
3. Transcript ingestion and source-aware retrieval
4. Provider adapters and grounded agent routing
5. Ship 30 skill and artifact contracts
6. Polished frontend and safe viewer
7. Automated evaluation, operational hardening, and handoff

