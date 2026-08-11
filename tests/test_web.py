from fastapi.testclient import TestClient

from main import app


def test_web_interface_is_available_and_responsive() -> None:
    with TestClient(app) as client:
        response = client.get("/ui")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Nexus AI Workspace" in response.text
    assert "viewport" in response.text
    assert "data-tab=\"chat\"" in response.text


def test_web_interface_preserves_backend_endpoints() -> None:
    with TestClient(app) as client:
        assert client.get("/").json()["message"] == "Nexus AI Backend is running"
        assert client.get("/health").json()["status"] == "ok"
