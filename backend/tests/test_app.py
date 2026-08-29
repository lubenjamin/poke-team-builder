from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_teams_requires_client_id_header() -> None:
    response = client.get("/api/teams")
    assert response.status_code == 400
