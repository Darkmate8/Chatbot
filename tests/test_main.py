from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend import main

CHAT_ID = "3f9c2a7e-1b4d-4c8a-9e2f-5a6b7c8d9e0f"  # what crypto.randomUUID() makes in the browser
HISTORY = [
    {"role": "user", "content": "the chai at hashtag was nice"},
    {"role": "bot", "content": "What made it nice?"},
]


@pytest.fixture
def fake(monkeypatch):
    """Fake DB and LLM: records every call, never touches Turso or Gemini."""
    calls = {"saved": [], "history_for": [], "llm": [], "result": ("Coffee Nation sounds different.", "coffee_nation", False)}

    def respond(history, message, cafe_context, entry_cafe):
        calls["llm"].append(
            {"history": history, "message": message, "cafe_context": cafe_context,
             "entry_cafe": entry_cafe, "at": datetime.now(timezone.utc)}
        )
        return calls["result"]

    def get_messages(chat_id):
        calls["history_for"].append(chat_id)
        return HISTORY

    monkeypatch.setattr(main.db, "insert_message", lambda *args, **kwargs: calls["saved"].append((args, kwargs)))
    monkeypatch.setattr(main.db, "get_messages", get_messages)
    monkeypatch.setattr(main.safety, "respond", respond)
    return calls


client = TestClient(main.app)


def post(chat_id=CHAT_ID, cafe="hashtag", message="but coffee nation was louder", **kwargs):
    return client.post("/chat", json={"chat_id": chat_id, "cafe": cafe, "message": message}, **kwargs)


def test_returns_reply_and_saves_both_rows_with_gemini_tag(fake):
    res = post()

    assert res.status_code == 200
    assert res.json() == {"reply": "Coffee Nation sounds different."}
    [(user_args, user_kwargs), (bot_args, bot_kwargs)] = fake["saved"]
    assert user_args == (CHAT_ID, "user", "but coffee nation was louder", "coffee_nation")
    assert bot_args == (CHAT_ID, "bot", "Coffee Nation sounds different.", "coffee_nation")
    assert user_kwargs["crisis"] is False
    assert bot_kwargs == {"crisis": False}


def test_crisis_turn_is_flagged_on_both_rows(fake):
    fake["result"] = ("CARE", "unknown", True)

    res = post(message="I don't want to be here anymore")

    assert res.json() == {"reply": "CARE"}
    [(user_args, user_kwargs), (bot_args, bot_kwargs)] = fake["saved"]
    assert user_args[3] == bot_args[3] == "unknown"
    assert user_kwargs["crisis"] is True and bot_kwargs["crisis"] is True


def test_user_row_keeps_arrival_time_not_save_time(fake):
    post()

    [(_, user_kwargs), _] = fake["saved"]
    assert user_kwargs["now"] <= fake["llm"][0]["at"]


def test_sends_chat_history_entry_cafe_and_all_cafe_info_to_llm(fake):
    post()

    assert fake["history_for"] == [CHAT_ID]
    [call] = fake["llm"]
    assert call["history"] == HISTORY
    assert call["message"] == "but coffee nation was louder"
    assert call["entry_cafe"] == "hashtag"
    assert "## Barsha (barsha)" in call["cafe_context"]


@pytest.mark.parametrize("cafe", ["hashtag", "coffee_nation", "juice_press", "barsha"])
def test_any_of_the_four_cafes_works_even_without_a_context_file(fake, cafe):
    assert post(cafe=cafe).status_code == 200


def test_does_not_store_ip_or_headers(fake):
    post(headers={"User-Agent": "SecretBrowser/1.0", "X-Forwarded-For": "203.0.113.5"})

    stored = repr(fake["saved"])
    assert "SecretBrowser" not in stored
    assert "203.0.113.5" not in stored
    assert "testclient" not in stored  # TestClient's fake client host


@pytest.mark.parametrize("cafe", ["starbucks", "unknown"])
def test_unknown_cafe_is_rejected_and_nothing_saved(fake, cafe):
    assert post(cafe=cafe).status_code == 400
    assert fake["saved"] == []


@pytest.mark.parametrize("chat_id", ["abc123", "priya@flame.edu.in", ""])
def test_chat_id_must_be_a_random_uuid(fake, chat_id):
    assert post(chat_id=chat_id).status_code == 422
    assert fake["saved"] == []
