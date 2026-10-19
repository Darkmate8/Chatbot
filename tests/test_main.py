import pytest
from fastapi.testclient import TestClient

from backend import main

CHAT_ID = "3f9c2a7e-1b4d-4c8a-9e2f-5a6b7c8d9e0f"  # what crypto.randomUUID() makes in the browser


@pytest.fixture
def saved(monkeypatch):
    """Fake DB and LLM: records every saved row, never touches Turso or Gemini."""
    rows = []
    monkeypatch.setattr(main.db, "insert_message", lambda *args, **kwargs: rows.append((args, kwargs)))
    monkeypatch.setattr(main.llm, "get_reply", lambda message, cafe_context: ("That sounds cosy.", "hashtag"))
    return rows


client = TestClient(main.app)


def test_chat_saves_user_and_bot_rows_and_returns_reply(saved):
    res = client.post("/chat", json={"chat_id": CHAT_ID, "cafe": "hashtag", "message": "the chai was nice"})

    assert res.status_code == 200
    assert res.json() == {"reply": "That sounds cosy."}
    assert saved == [
        ((CHAT_ID, "user", "the chai was nice", "hashtag"), {}),
        ((CHAT_ID, "bot", "That sounds cosy.", "hashtag"), {}),
    ]


def test_chat_does_not_store_ip_or_headers(saved):
    client.post(
        "/chat",
        json={"chat_id": CHAT_ID, "cafe": "hashtag", "message": "hi"},
        headers={"User-Agent": "SecretBrowser/1.0", "X-Forwarded-For": "203.0.113.5"},
    )

    stored = repr(saved)
    assert "SecretBrowser" not in stored
    assert "203.0.113.5" not in stored
    assert "testclient" not in stored  # TestClient's fake client host


def test_unknown_cafe_is_rejected_and_nothing_saved(saved):
    res = client.post("/chat", json={"chat_id": CHAT_ID, "cafe": "starbucks", "message": "hi"})

    assert res.status_code == 400
    assert saved == []


@pytest.mark.parametrize("chat_id", ["abc123", "priya@flame.edu.in", ""])
def test_chat_id_must_be_a_random_uuid(saved, chat_id):
    res = client.post("/chat", json={"chat_id": chat_id, "cafe": "hashtag", "message": "hi"})

    assert res.status_code == 422
    assert saved == []
