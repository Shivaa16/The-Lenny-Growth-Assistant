from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from lenny_api.main import app
from lenny_api.sessions.dependencies import get_session_service
from lenny_api.sessions.exceptions import PersistenceUnavailableError, SessionNotFoundError


class FailingSessionService:
    async def list_sessions(self, user_id: str, *, limit: int, offset: int):
        raise PersistenceUnavailableError


class MissingSessionService:
    async def get_session(self, session_id: UUID):
        raise SessionNotFoundError(session_id)


def test_blank_session_title_returns_structured_validation_error() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/sessions", json={"title": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_missing_session_returns_structured_not_found() -> None:
    session_id = uuid4()
    app.dependency_overrides[get_session_service] = lambda: MissingSessionService()
    try:
        response = TestClient(app).get(f"/api/v1/sessions/{session_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "session_not_found"


def test_database_failure_returns_actionable_service_unavailable() -> None:
    app.dependency_overrides[get_session_service] = lambda: FailingSessionService()
    try:
        response = TestClient(app).get("/api/v1/sessions")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "persistence_unavailable"

