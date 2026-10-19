import json
import re
from types import SimpleNamespace

import pytest

from backend import safety
from tests.fakes import FakeGemini


@pytest.fixture(autouse=True)
def gemini_model(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "fake-model")


def product_md_block(heading):
    with open("PRODUCT.md") as f:
        section = f.read().split(heading)[1]
    return re.search(r"```\n(.*?)```", section, re.S).group(1)


def test_classifier_prompt_matches_product_md():
    assert safety.CLASSIFIER_PROMPT == product_md_block("### Crisis classifier prompt")


def test_care_reply_matches_product_md():
    assert safety.CARE_REPLY == product_md_block("### Care reply").strip()


def test_care_reply_includes_tele_manas():
    assert "14416" in safety.CARE_REPLY


def test_crisis_true_from_gemini():
    fake = FakeGemini(json.dumps({"crisis": True}))

    assert safety.is_crisis("I don't want to be here anymore", client=fake) is True
    [call] = fake.calls
    assert call["model"] == "fake-model"
    assert call["contents"] == "I don't want to be here anymore"
    assert call["config"].system_instruction == safety.CLASSIFIER_PROMPT


def test_crisis_false_from_gemini():
    assert safety.is_crisis("the fries were great", client=FakeGemini(json.dumps({"crisis": False}))) is False


@pytest.mark.parametrize(
    "response",
    [RuntimeError("503 high demand"), "not json", json.dumps({"other": 1}), json.dumps({"crisis": "no"}), None],
)
def test_any_failure_counts_as_crisis(response):
    assert safety.is_crisis("hi", client=FakeGemini(response)) is True


@pytest.fixture
def persona(monkeypatch):
    """Fake persona reply; records whether it was asked."""
    calls = []

    def set_reply(reply, cafe="hashtag"):
        def get_reply(history, message, cafe_context, entry_cafe):
            calls.append(message)
            return reply, cafe
        monkeypatch.setattr(safety.llm, "get_reply", get_reply)

    set_reply("That sounds cosy. What made it nice?")
    return SimpleNamespace(calls=calls, set_reply=set_reply)


def test_crisis_gets_care_reply_and_skips_persona(monkeypatch, persona):
    monkeypatch.setattr(safety, "is_crisis", lambda message: True)

    assert safety.respond([], "I want to disappear", "ctx", "hashtag") == (safety.CARE_REPLY, "unknown", True)
    assert persona.calls == []


def test_normal_message_gets_persona_reply(monkeypatch, persona):
    monkeypatch.setattr(safety, "is_crisis", lambda message: False)

    assert safety.respond([], "the chai was nice", "ctx", "hashtag") == (
        "That sounds cosy. What made it nice?", "hashtag", False,
    )


@pytest.mark.parametrize("empty", [None, ""])
def test_persona_with_no_text_falls_back_to_care_reply(monkeypatch, persona, empty):
    monkeypatch.setattr(safety, "is_crisis", lambda message: False)
    persona.set_reply(empty, "unknown")

    assert safety.respond([], "hi", "ctx", "hashtag") == (safety.CARE_REPLY, "unknown", True)
