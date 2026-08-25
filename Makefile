.PHONY: setup-models sync-transcripts ingest-transcripts ingest-demo up down migrate api-test web-build smoke

setup-models:
	ollama pull qwen2.5:0.5b
	ollama pull nomic-embed-text

sync-transcripts:
	cd apps/api && python -m lenny_api.knowledge.sync

ingest-transcripts:
	cd apps/api && python -m lenny_api.knowledge.cli

ingest-demo:
	cd apps/api && python -m lenny_api.knowledge.cli --limit 25

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

smoke:
	powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
