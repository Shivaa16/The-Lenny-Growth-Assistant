.PHONY: setup-models up down migrate api-test web-build

setup-models:
	ollama pull qwen2.5:3b
	ollama pull nomic-embed-text

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
