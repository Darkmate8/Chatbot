import json
import re
import pytest

from backend import llm
from tests.fakes import FakeGemini


@pytest.fixture(autouse=True)
def gemini_model(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "fake-model")


def test_prompt_template_matches_product_md():
    with open("PRODUCT.md") as f:
        section = f.read().split("## System prompt and safety layer")[1]
    documented = re.search(r"```\n(.*?)```", section, re.S).group(1)

    assert llm.SYSTEM_PROMPT_TEMPLATE == documented


def test_system_prompt_fills_cafe_info_and_entry_cafe():
    prompt = llm.build_system_prompt("## Hashtag (hashtag)\nServes chai.", "hashtag")

    assert "## Hashtag (hashtag)\nServes chai." in prompt
    assert "link for: hashtag" in prompt
    assert "{cafe_context}" not in prompt and "{entry_cafe}" not in prompt


def test_sends_history_then_new_message():
    fake = FakeGemini(json.dumps({"reply": "Nice.", "cafe": "hashtag"}))
    history = [
        {"role": "user", "content": "the chai was nice"},
        {"role": "bot", "content": "What made it nice?"},
    ]

    llm.get_reply(history, "it was warm", "cafe info", "hashtag", client=fake)

    [call] = fake.calls
    assert [(c.role, c.parts[0].text) for c in call["contents"]] == [
        ("user", "the chai was nice"),
        ("model", "What made it nice?"),
        ("user", "it was warm"),
    ]
    assert call["model"] == "fake-model"
    assert "cafe info" in call["config"].system_instruction


def test_returns_reply_and_cafe_from_json():
    fake = FakeGemini(json.dumps({"reply": "That sounds cosy.", "cafe": "coffee_nation"}))

    assert llm.get_reply([], "hi", "ctx", "hashtag", client=fake) == ("That sounds cosy.", "coffee_nation")


def test_malformed_json_returns_raw_text_and_unknown():
    fake = FakeGemini("Sorry, not JSON")

    assert llm.get_reply([], "hi", "ctx", "hashtag", client=fake) == ("Sorry, not JSON", "unknown")


def test_cafe_outside_allowed_list_becomes_unknown():
    fake = FakeGemini(json.dumps({"reply": "Nice!", "cafe": "starbucks"}))

    assert llm.get_reply([], "hi", "ctx", "hashtag", client=fake) == ("Nice!", "unknown")


def test_only_the_last_five_earlier_messages_are_sent():
    fake = FakeGemini(json.dumps({"reply": "Nice.", "cafe": "hashtag"}))
    history = [{"role": "user" if i % 2 == 0 else "bot", "content": f"msg {i}"} for i in range(8)]

    llm.get_reply(history, "new message", "ctx", "hashtag", client=fake)

    sent = [c.parts[0].text for c in fake.calls[0]["contents"]]
    assert sent == ["msg 3", "msg 4", "msg 5", "msg 6", "msg 7", "new message"]


def test_transcription_prompt_matches_product_md():
    with open("PRODUCT.md") as f:
        section = f.read().split("### Transcription prompt")[1]
    documented = re.search(r"```\n(.*?)```", section, re.S).group(1)

    assert llm.TRANSCRIBE_PROMPT == documented


def test_transcribe_sends_audio_bytes_and_returns_text():
    fake = FakeGemini(json.dumps({"text": "the chai was nice"}))

    assert llm.transcribe(b"fake-audio", "audio/webm", client=fake) == "the chai was nice"
    [call] = fake.calls
    assert call["model"] == "fake-model"
    assert call["config"].system_instruction == llm.TRANSCRIBE_PROMPT
    [part] = call["contents"]
    assert part.inline_data.data == b"fake-audio"
    assert part.inline_data.mime_type == "audio/webm"


def test_transcribe_strips_whitespace_and_allows_empty():
    assert llm.transcribe(b"x", "audio/webm", client=FakeGemini(json.dumps({"text": "  hi \n"}))) == "hi"
    assert llm.transcribe(b"x", "audio/webm", client=FakeGemini(json.dumps({"text": ""}))) == ""


@pytest.mark.parametrize("bad", ["not json", json.dumps({"words": "hi"}), json.dumps({"text": 5}), None])
def test_transcribe_raises_on_bad_output(bad):
    with pytest.raises(llm.TranscriptionError):
        llm.transcribe(b"x", "audio/webm", client=FakeGemini(bad))
