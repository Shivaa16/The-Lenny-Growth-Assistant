# 2–3 Minute Demo Script

Keep the camera enabled throughout. Close unrelated windows and notifications. Start with healthy containers, Ollama running, and a prebuilt transcript index.

## 0:00–0:25 — Problem and judgment

“Product and growth teams want to use hundreds of Lenny’s Podcast interviews, but searching episodes manually is slow and synthesized advice easily loses its source. I built the Lenny Growth Assistant to produce reusable, source-backed answers without exposing prompts or infrastructure. I prioritized trust and operability over broad autonomous tooling.”

Show the white/blue first-run UI and the visible `Local · qwen2.5:3b` provider badge.

## 0:25–1:10 — Grounded local conversation

Ask: `How should an early-stage product build and measure a growth loop?`

While it runs: “This demo uses Ollama locally. The API embeds the question, combines pgvector similarity with PostgreSQL full-text ranking, applies a grounding threshold, and only then calls the model.”

Open one source card. Ask: `Which step should a two-person team start with?` Point out persisted follow-up context and new citations.

## 1:10–1:45 — Dedicated artifact skill

Choose **Ship 30 essay**.

“This is a separate skill boundary, not a one-off prompt. It encodes the assignment-linked framework: specific audience, curator credibility, one 4A lens, and a consistent steps-or-lessons structure. The essay and its source manifest persist with the session.”

Briefly show **HTML brief** and the side-by-side viewer.

## 1:45–2:15 — Trust and technical trade-off

“Generated HTML is untrusted. The server removes scripts, handlers, forms, embeds, and unsafe attributes. The browser then renders sanitized content in an iframe with an empty sandbox and restrictive CSP.”

“My main trade-off was choosing a 3B local model. It fits a 16 GB laptop and keeps the demo private, but synthesis quality is lower than Claude. The provider interface allows cloud Claude without changing product code, while retrieval and citation rules remain identical.”

## 2:15–2:40 — Operability and close

Show `docker compose ps`, the successful smoke test, and the repository README.

“A fresh evaluator gets Compose startup, automatic migrations, service health checks, incremental indexing, 32 automated tests, CI, and a troubleshooting runbook. Unsupported questions refuse to invent an answer. That is the core deployment promise: useful, inspectable, and operable.”

End on the product, not the terminal.
