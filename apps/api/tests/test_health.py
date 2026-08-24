from fastapi.testclient import TestClient

from lenny_api.main import app

client = TestClient(app)


def test_liveness_contract() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "lenny-growth-api",
        "version": "0.1.0",
    }
    assert response.headers["X-Request-ID"]


def test_provider_config_hides_secrets() -> None:
    response = client.get("/api/v1/config")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "ollama"
    assert body["model"] == "qwen2.5:3b"
    assert "database_url" not in body
    assert "anthropic_api_key" not in body


def test_readiness_reports_database_outage(monkeypatch) -> None:
    async def unavailable() -> bool:
        return False

    monkeypatch.setattr("lenny_api.main.database_is_ready", unavailable)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
