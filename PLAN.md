# Slice 1: one message in, one reply out, both saved

**A student can:** send one message about Hashtag and get a Gemini reply,
with both messages saved in Turso. Ugly but end-to-end.

**Out of scope (later slices):** web page, consent screen, other three cafes,
safety check, voice, gender, cafe auto-tagging.

Proof tags: `[CODE]` = provable from the diff and test output.
`[VERIFY]` = needs the app actually running. `[MANUAL]` = I check by hand;
never auto-marked done.

## Before starting the goal (do these yourself)

- [x] Create a Turso database; put `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` in `.env`
- [ ] Create a paid-tier Gemini key; put `GEMINI_API_KEY` and `GEMINI_MODEL` in `.env`
- [x] Create `.gitignore` containing `.env`, then `git init` and make a first commit
- [x] Write `cafes/hashtag.md` yourself (10 to 15 lines: menu, books, seating, vibe; no invented details)
- [x] Run this once in the Turso shell:

```sql
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'bot')),
  content TEXT NOT NULL,
  created_at TEXT NOT NULL,
  local_hour INTEGER NOT NULL,
  cafe TEXT NOT NULL,
  input_mode TEXT NOT NULL DEFAULT 'text',
  gender TEXT,
  gender_source TEXT,
  consent_version TEXT
);
```

- [x] Commit again (this is your rollback point)

## Tasks (each 2 to 5 minutes)

- [ ] **T1 `[CODE]`** `backend/db.py`: `insert_message(chat_id, role, content, cafe)` (fills `created_at` in UTC and `local_hour` in IST) and `get_messages(chat_id)`. Test: `tests/test_db.py` inserts two rows with a random chat_id, reads them back, deletes them. Verify: `pytest tests/test_db.py` passes.
- [ ] **T2 `[CODE]`** `backend/cafes.py`: `load_cafe_context(cafe)` reads `cafes/<cafe>.md`; an unknown cafe raises a clear error. Test: `tests/test_cafes.py`. Verify: `pytest tests/test_cafes.py` passes.
- [ ] **T3 `[CODE]`** `backend/llm.py`: build the system prompt from the "System prompt and safety layer" section of PRODUCT.md, call Gemini, parse the JSON `{reply, cafe}`. If the JSON is malformed, return the raw text as the reply and `unknown`. Test with a fake Gemini client (no real calls). Verify: `pytest tests/test_llm.py` passes.
- [ ] **T4 `[CODE]`** `backend/main.py`: `POST /chat` takes `{chat_id, cafe, message}`, saves the user row, calls the LLM, saves the bot row, returns `{reply}`. No IP, header or user-agent is read or stored. Test with the DB and LLM faked. Verify: `pytest` passes in full.
- [ ] **T5 `[VERIFY]`** Run the server, `curl` one message with `cafe=hashtag`, show the reply, then query Turso and show exactly two rows for that chat_id with the right cafe and role. Confirm the table has no IP, name or email column.
- [ ] **T6 `[MANUAL]`** I send 5 different messages and read the replies: warm, no advice, one question, at most 3 sentences, no invented cafe details. Not auto-marked done.

**Advisor checkpoint:** consult the stronger model before T1 (schema and privacy) and after T4 (the one place an identifier could sneak in).

## Goal condition (paste into `/goal`)

```
Slice 1 in PLAN.md is done when all of these are shown in the transcript: (1) the full `pytest` run passes with 0 failures; (2) a curl POST to /chat with cafe=hashtag returned a JSON reply; (3) a query on the messages table shows exactly one user row and one bot row for that chat_id, with cafe=hashtag, and the table has no column for IP, name or email; (4) tasks T1 to T5 are ticked in PLAN.md. Do not tick T6. Stop after 20 turns if not done.
```

## After the goal clears

- [ ] Read the diffs on `backend/db.py` and `backend/main.py` yourself, line by line
- [ ] Do T6 by hand
- [ ] Explain without looking back: why does the app store a random `chat_id` at all? (Answer in 2 sentences, then check it against PRODUCT.md)
- [ ] Debug one real bug yourself (stack trace, hypothesis, test) before asking Claude Code
- [ ] Commit; any repeatable mistake goes into the CLAUDE.md ledger
