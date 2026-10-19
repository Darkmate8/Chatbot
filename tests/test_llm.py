import json
import re
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
