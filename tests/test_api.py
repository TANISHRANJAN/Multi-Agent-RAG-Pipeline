from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient
import api

client = TestClient(api.app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["chunks_file_exists"], bool)
    assert isinstance(body["faiss_index_exists"], bool)


def test_query_rejects_empty_question():
    response = client.post("/query", json={"question": "", "top_k": 4})
    assert response.status_code == 422


def test_query_rejects_top_k_out_of_range():
    response = client.post("/query", json={"question": "Where is my order?", "top_k": 100})
    assert response.status_code == 422


def test_feedback_rejects_invalid_rating():
    response = client.post(
        "/feedback",
        json={
            "question": "Test question",
            "answer": "Test answer",
            "rating": "neutral",
            "comment": "Should fail schema validation",
        },
    )
    assert response.status_code == 422


def test_feedback_endpoint_accepts_valid_feedback(monkeypatch):
    # Avoid writing a real feedback file during automated tests.
    monkeypatch.setattr(
        api,
        "save_feedback",
        lambda **kwargs: {"status": "saved", "rating": kwargs["rating"]},
    )
    response = client.post(
        "/feedback",
        json={
            "question": "Where is my order?",
            "answer": "Use the order tracking page.",
            "rating": "positive",
            "comment": "Test feedback",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    assert response.json()["rating"] == "positive"
