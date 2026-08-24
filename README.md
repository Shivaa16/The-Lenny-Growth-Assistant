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

Setup and run instructions will be completed as the application foundation is wired.

