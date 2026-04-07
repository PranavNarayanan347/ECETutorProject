from fastapi.testclient import TestClient

from services.api.main import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["api"] == "ok"


def test_chat_without_docs_returns_clarify():
    client = TestClient(app)
    response = client.post(
        "/chat",
        json={
            "session_id": "s1",
            "course_id": "ece101",
            "message": "Explain KCL",
            "allow_full_solution": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "response_type" in data
    assert data["confidence"] <= 1.0
