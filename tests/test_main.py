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


def post(chat_id=CHAT_ID, cafe="hashtag", message="but coffee nation was louder", consent_version=main.CONSENT_VERSION, input_mode=None, **kwargs):
    body = {"chat_id": chat_id, "cafe": cafe, "message": message, "consent_version": consent_version}
    if input_mode is not None:
        body["input_mode"] = input_mode
    return client.post("/chat", json=body, **kwargs)


def test_returns_reply_and_saves_both_rows_with_gemini_tag(fake):
    res = post()

    assert res.status_code == 200
    assert res.json() == {"reply": "Coffee Nation sounds different."}
    [(user_args, user_kwargs), (bot_args, bot_kwargs)] = fake["saved"]
    assert user_args == (CHAT_ID, "user", "but coffee nation was louder", "coffee_nation")
    assert bot_args == (CHAT_ID, "bot", "Coffee Nation sounds different.", "coffee_nation")
    assert user_kwargs["crisis"] is False
    assert user_kwargs["consent_version"] == "v2-draft"
    assert bot_kwargs == {"crisis": False, "consent_version": "v2-draft"}


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


def test_unrecognised_cafe_is_rejected_and_nothing_saved(fake):
    assert post(cafe="starbucks").status_code == 400
    assert fake["saved"] == []


def test_unknown_entry_cafe_is_accepted_for_links_without_cafe(fake):
    assert post(cafe="unknown").status_code == 200
    assert fake["llm"][0]["entry_cafe"] == "unknown"


@pytest.mark.parametrize("version", ["v0-old", ""])
def test_wrong_consent_version_is_rejected_and_nothing_saved(fake, version):
    assert post(consent_version=version).status_code == 400
    assert fake["saved"] == []


def test_missing_consent_version_is_rejected(fake):
    res = client.post("/chat", json={"chat_id": CHAT_ID, "cafe": "hashtag", "message": "hi"})
    assert res.status_code == 422
    assert fake["saved"] == []


@pytest.mark.parametrize("chat_id", ["abc123", "priya@flame.edu.in", ""])
def test_chat_id_must_be_a_random_uuid(fake, chat_id):
    assert post(chat_id=chat_id).status_code == 422
    assert fake["saved"] == []


def test_rejects_messages_over_2000_characters(fake):
    assert post(message="a" * 2000).status_code == 200
    assert post(message="a" * 2001).status_code == 422
    assert len(fake["llm"]) == 1  # the long one never reached Gemini


def test_input_mode_defaults_to_text_on_both_rows(fake):
    post()

    [(_, user_kwargs), (_, bot_kwargs)] = fake["saved"]
    assert user_kwargs["input_mode"] == "text"
    assert bot_kwargs.get("input_mode", "text") == "text"


def test_voice_input_mode_is_saved_on_user_row_only(fake):
    post(input_mode="voice")

    [(_, user_kwargs), (_, bot_kwargs)] = fake["saved"]
    assert user_kwargs["input_mode"] == "voice"
    assert bot_kwargs.get("input_mode", "text") == "text"


def test_unknown_input_mode_is_rejected(fake):
    assert post(input_mode="video").status_code == 422
    assert fake["saved"] == []


@pytest.fixture
def fake_transcribe(monkeypatch):
    calls = {"audio": [], "result": "the chai was nice"}

    def transcribe(audio, mime_type):
        calls["audio"].append((audio, mime_type))
        if isinstance(calls["result"], Exception):
            raise calls["result"]
        return calls["result"]

    monkeypatch.setattr(main.llm, "transcribe", transcribe)
    return calls


def post_audio(audio=b"fake-audio", content_type="audio/webm;codecs=opus", **kwargs):
    return client.post("/transcribe", content=audio, headers={"Content-Type": content_type, **kwargs.pop("headers", {})}, **kwargs)


def test_transcribe_returns_text_and_sends_raw_audio(fake_transcribe):
    res = post_audio()

    assert res.status_code == 200
    assert res.json() == {"text": "the chai was nice"}
    assert fake_transcribe["audio"] == [(b"fake-audio", "audio/webm")]  # codecs part dropped


@pytest.mark.parametrize("content_type", ["audio/webm", "audio/ogg", "audio/mp4", "AUDIO/MP4"])
def test_transcribe_accepts_browser_recording_types(fake_transcribe, content_type):
    assert post_audio(content_type=content_type).status_code == 200


@pytest.mark.parametrize("content_type", ["video/mp4", "application/json", "text/plain"])
def test_transcribe_rejects_other_types_before_gemini(fake_transcribe, content_type):
    assert post_audio(content_type=content_type).status_code == 415
    assert fake_transcribe["audio"] == []


def test_transcribe_rejects_audio_over_2_mb_before_gemini(fake_transcribe):
    assert post_audio(audio=b"a" * main.MAX_AUDIO_BYTES).status_code == 200
    assert post_audio(audio=b"a" * (main.MAX_AUDIO_BYTES + 1)).status_code == 413
    assert len(fake_transcribe["audio"]) == 1


def test_transcribe_rejects_empty_body(fake_transcribe):
    assert post_audio(audio=b"").status_code == 400
    assert fake_transcribe["audio"] == []


def test_transcribe_cuts_text_to_message_limit(fake_transcribe):
    fake_transcribe["result"] = "a" * (main.MAX_MESSAGE_LENGTH + 50)

    assert len(post_audio().json()["text"]) == main.MAX_MESSAGE_LENGTH


@pytest.mark.parametrize("error", [main.llm.TranscriptionError("bad"), RuntimeError("503 UNAVAILABLE")])
def test_transcribe_gemini_failure_is_a_friendly_502(fake_transcribe, error):
    fake_transcribe["result"] = error

    res = post_audio()

    assert res.status_code == 502
    assert "try again" in res.json()["detail"]


def test_transcribe_stores_nothing(fake, fake_transcribe):
    post_audio()

    assert fake["saved"] == []
