import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import turso_serverless

ALLOWED_CAFES = {"hashtag", "coffee_nation", "juice_press", "barsha", "unknown"}
IST = ZoneInfo("Asia/Kolkata")


def get_connection():
    return turso_serverless.connect(
        os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )


def insert_message(chat_id, role, content, cafe, now=None, crisis=False, consent_version=None):
    if cafe not in ALLOWED_CAFES:
        raise ValueError(f"Unknown cafe: {cafe!r}")
    now = now or datetime.now(timezone.utc)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO messages"
            " (chat_id, role, content, created_at, local_hour, cafe, crisis, consent_version)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (chat_id, role, content, now.isoformat(), now.astimezone(IST).hour, cafe, int(crisis), consent_version),
        )
        conn.commit()
    finally:
        conn.close()


def get_messages(chat_id):
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT chat_id, role, content, created_at, local_hour, cafe, crisis, consent_version"
            " FROM messages WHERE chat_id = ? ORDER BY id",
            (chat_id,),
        )
        columns = [c[0] for c in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()
