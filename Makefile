.PHONY: setup-models sync-transcripts ingest-transcripts up down migrate api-test web-build

setup-models:
	ollama pull qwen2.5:3b
	ollama pull nomic-embed-text

sync-transcripts:
	cd apps/api && python -m lenny_api.knowledge.sync

ingest-transcripts:
	cd apps/api && python -m lenny_api.knowledge.cli

up:
	docker compose up --build

down:
	docker compose down

migrate:
	cd apps/api && alembic upgrade head

api-test:
	cd apps/api && pytest

web-build:
	cd apps/web && npm run build
