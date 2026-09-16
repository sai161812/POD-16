from fastapi.testclient import TestClient

from app.main import app


def test_v1_requires_api_key() -> None:
    client = TestClient(app)
    response = client.get("/v1/projects")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "unauthorized"
    assert payload["error"]["request_id"]
