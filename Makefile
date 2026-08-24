.PHONY: setup-models up down api-test web-build

setup-models:
	ollama pull qwen2.5:3b
	ollama pull nomic-embed-text

up:
	docker compose up --build

down:
	docker compose down

api-test:
	cd apps/api && pytest

web-build:
	cd apps/web && npm run build

