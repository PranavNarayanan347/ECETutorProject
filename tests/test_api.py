from fastapi.testclient import TestClient

from services.api.main import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["api"] == "ok"


def test_chat_without_docs_returns_response():
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
    assert "content" in data
    assert data["confidence"] <= 1.0


def test_auth_register_and_login():
    client = TestClient(app)
    reg = client.post(
        "/auth/register",
        json={"user_id": "testuser1", "password": "pass123", "role": "student"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]

    login = client.post(
        "/auth/login",
        json={"user_id": "testuser1", "password": "pass123"},
    )
    assert login.status_code == 200
    assert login.json()["role"] == "student"


def test_ingest_requires_auth():
    client = TestClient(app)
    response = client.post(
        "/ingest",
        data={"course_id": "ece101", "title": "test"},
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 401


def test_ingest_with_instructor_auth():
    client = TestClient(app)
    reg = client.post(
        "/auth/register",
        json={"user_id": "prof1", "password": "pass123", "role": "instructor"},
    )
    token = reg.json()["access_token"]
    response = client.post(
        "/ingest",
        data={"course_id": "ece101", "title": "test doc"},
        files={"file": ("test.txt", b"Ohm's law V = IR", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "complete"
