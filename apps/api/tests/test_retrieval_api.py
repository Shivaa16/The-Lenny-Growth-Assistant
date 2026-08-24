from fastapi.testclient import TestClient

from lenny_api.knowledge.dependencies import get_retrieval_service
from lenny_api.knowledge.embeddings import EmbeddingProviderError
from lenny_api.main import app


class EmptyRetrievalService:
    async def search(self, query: str, *, limit: int):
        return []


class OfflineRetrievalService:
    async def search(self, query: str, *, limit: int):
        raise EmbeddingProviderError


def test_empty_retrieval_explicitly_reports_ungrounded() -> None:
    app.dependency_overrides[get_retrieval_service] = lambda: EmptyRetrievalService()
    try:
        response = TestClient(app).post(
            "/api/v1/retrieval/search", json={"query": "unsupported question"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "query": "unsupported question",
        "evidence": [],
        "grounded": False,
    }


def test_unavailable_ollama_returns_actionable_error() -> None:
    app.dependency_overrides[get_retrieval_service] = lambda: OfflineRetrievalService()
    try:
        response = TestClient(app).post(
            "/api/v1/retrieval/search", json={"query": "growth loops"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "embedding_provider_unavailable"

