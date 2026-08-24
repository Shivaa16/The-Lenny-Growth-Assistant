from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from lenny_api.agent.types import GenerationResult
from lenny_api.artifacts.dependencies import get_artifact_repository, get_artifact_service
from lenny_api.artifacts.sanitizer import sanitize_html
from lenny_api.artifacts.service import Ship30ArtifactService
from lenny_api.knowledge.repository import RetrievedEvidence
from lenny_api.main import app


class FakeRepository:
    def __init__(self) -> None:
        self.saved = None

    async def require_session(self, session_id):
        return SimpleNamespace(id=session_id)

    async def save(self, artifact):
        self.saved = artifact
        return artifact


class FakeRetrieval:
    def __init__(self, evidence):
        self.evidence = evidence

    async def search(self, query, *, limit):
        assert limit == 8
        return self.evidence


class FakeProvider:
    def __init__(self) -> None:
        self.system_prompt = ""

    async def generate(self, *, system_prompt, messages):
        self.system_prompt = system_prompt
        assert messages[0].content.startswith("Essay topic:")
        return GenerationResult(
            content="# A better growth loop\n\nBuild one loop at a time [1].",
            provider="ollama",
            model="qwen",
            usage={"tokens": 42},
        )


def evidence() -> RetrievedEvidence:
    return RetrievedEvidence(
        chunk_id=uuid4(),
        source_id=uuid4(),
        content="A loop should create its own next input.",
        title="Growth loops",
        guest="A. Guest",
        youtube_url="https://youtube.com/watch?v=test",
        repository_path="episodes/growth.txt",
        ordinal=1,
        semantic_score=0.9,
        keyword_score=0.5,
        score=0.85,
    )


@pytest.mark.asyncio
async def test_ship30_skill_is_grounded_and_persists_metadata() -> None:
    repository = FakeRepository()
    provider = FakeProvider()
    service = Ship30ArtifactService(repository, FakeRetrieval([evidence()]), provider)

    artifact = await service.create(uuid4(), "How growth loops compound", "markdown")

    assert "approximately 1,250-word essay" in provider.system_prompt
    assert artifact.artifact_metadata["skill"] == "ship-30-for-30"
    assert artifact.artifact_metadata["citations"][0]["title"] == "Growth loops"
    assert repository.saved is artifact


@pytest.mark.asyncio
async def test_empty_retrieval_never_calls_model() -> None:
    class UnexpectedProvider:
        async def generate(self, **kwargs):
            raise AssertionError("provider must not be called without evidence")

    service = Ship30ArtifactService(FakeRepository(), FakeRetrieval([]), UnexpectedProvider())
    artifact = await service.create(uuid4(), "Unknown subject", "markdown")

    assert "couldn't find enough support" in artifact.content
    assert artifact.artifact_metadata["provider"] == "grounding_guard"


def test_html_sanitizer_removes_executable_content_and_event_handlers() -> None:
    unsafe = (
        '<article onclick="steal()"><h1>Safe</h1>'
        "<script>alert(1)</script><p>Body</p></article>"
    )

    sanitized = sanitize_html(unsafe)

    assert sanitized == "<article><h1>Safe</h1><p>Body</p></article>"
    assert "onclick" not in sanitized
    assert "alert" not in sanitized


def artifact_response(session_id):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        session_id=session_id,
        message_id=None,
        kind="markdown",
        title="Growth loops",
        content="# Growth loops",
        sanitized_content="# Growth loops",
        artifact_metadata={"skill": "ship-30-for-30", "citations": []},
        created_at=now,
        updated_at=now,
    )


def test_create_artifact_api_returns_typed_artifact() -> None:
    session_id = uuid4()

    class FakeService:
        async def create(self, requested_session_id, topic, kind):
            assert requested_session_id == session_id
            assert topic == "Growth loops"
            assert kind == "markdown"
            return artifact_response(session_id)

    app.dependency_overrides[get_artifact_service] = lambda: FakeService()
    try:
        response = TestClient(app).post(
            f"/api/v1/sessions/{session_id}/artifacts",
            json={"topic": "Growth loops", "kind": "markdown"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["artifact_metadata"]["skill"] == "ship-30-for-30"


def test_artifact_list_is_scoped_to_session() -> None:
    session_id = uuid4()

    class FakeArtifactRepository:
        async def list_for_session(self, requested_session_id):
            assert requested_session_id == session_id
            return [artifact_response(session_id)]

    app.dependency_overrides[get_artifact_repository] = lambda: FakeArtifactRepository()
    try:
        response = TestClient(app).get(f"/api/v1/sessions/{session_id}/artifacts")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["session_id"] == str(session_id)
