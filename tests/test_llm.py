import json
from types import SimpleNamespace

import pytest

from backend import llm


class FakeGemini:
    """Stands in for genai.Client: records the call, returns canned text."""

    def __init__(self, text):
        self.text = text
        self.calls = []
        self.models = self

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        return SimpleNamespace(text=self.text)


@pytest.fixture(autouse=True)
def gemini_model(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "fake-model")


def test_system_prompt_includes_cafe_context_and_persona():
    prompt = llm.build_system_prompt("Hashtag serves masala chai.")

    assert "Hashtag serves masala chai." in prompt
    assert "{cafe_context}" not in prompt
    assert "ONE\n  open-ended follow-up" in prompt
    assert "You are an AI, and you say\nso if asked." in prompt


def test_returns_reply_and_cafe_from_json():
    fake = FakeGemini(json.dumps({"reply": "That sounds cosy. What made it nice?", "cafe": "hashtag"}))

    reply, cafe = llm.get_reply("the chai was nice", "Hashtag info", client=fake)

    assert (reply, cafe) == ("That sounds cosy. What made it nice?", "hashtag")
    [call] = fake.calls
    assert call["model"] == "fake-model"
    assert call["contents"] == "the chai was nice"
    assert "Hashtag info" in call["config"].system_instruction


def test_malformed_json_returns_raw_text_and_unknown():
    fake = FakeGemini("Sorry, not JSON")

    assert llm.get_reply("hi", "ctx", client=fake) == ("Sorry, not JSON", "unknown")


def test_cafe_outside_allowed_list_becomes_unknown():
    fake = FakeGemini(json.dumps({"reply": "Nice!", "cafe": "starbucks"}))

    assert llm.get_reply("hi", "ctx", client=fake) == ("Nice!", "unknown")
