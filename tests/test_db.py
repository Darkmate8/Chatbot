import uuid
from datetime import datetime

import pytest

from backend import db


@pytest.fixture
def chat_id():
    # Random id so test rows never collide with real chats; cleaned up after.
    cid = f"test-{uuid.uuid4()}"
    yield cid
    conn = db.get_connection()
    conn.execute("DELETE FROM messages WHERE chat_id = ?", (cid,))
    conn.commit()
    conn.close()


def test_insert_two_messages_and_read_them_back(chat_id):
    db.insert_message(chat_id, "user", "the chai was nice", "hashtag")
    db.insert_message(chat_id, "bot", "That sounds cosy.", "hashtag")

    rows = db.get_messages(chat_id)

    assert [(r["role"], r["content"], r["cafe"]) for r in rows] == [
        ("user", "the chai was nice", "hashtag"),
        ("bot", "That sounds cosy.", "hashtag"),
    ]
    for r in rows:
        assert r["chat_id"] == chat_id
        assert datetime.fromisoformat(r["created_at"]).utcoffset().total_seconds() == 0
        assert 0 <= r["local_hour"] <= 23


def test_local_hour_is_ist(chat_id):
    # 20:00 UTC is 01:30 IST the next day, so local_hour must be 1.
    db.insert_message(chat_id, "user", "hi", "hashtag", now=datetime.fromisoformat("2026-10-19T20:00:00+00:00"))

    [row] = db.get_messages(chat_id)

    assert row["local_hour"] == 1
    assert row["created_at"] == "2026-10-19T20:00:00+00:00"


def test_rejects_unknown_cafe(chat_id):
    with pytest.raises(ValueError):
        db.insert_message(chat_id, "user", "hi", "starbucks")
    assert db.get_messages(chat_id) == []


def test_crisis_flag_is_stored_and_defaults_to_zero(chat_id):
    db.insert_message(chat_id, "user", "hi", "hashtag")
    db.insert_message(chat_id, "user", "I don't want to be here", "unknown", crisis=True)

    assert [r["crisis"] for r in db.get_messages(chat_id)] == [0, 1]
