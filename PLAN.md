# Slice 2: any of the four cafes, per-message cafe tag, chat memory

Slice 1 is done (commits ad15393, 3384486; its plan is in git history).

**A student can:** chat about any of the four cafes through `cafe` in the
request (the `?cafe=` link value), talk across several turns with the bot
remembering earlier messages, and compare cafes in one chat. Each message row
stores the cafe that message is about, as tagged by Gemini.

**Decisions (2026-10-19):**
- All four cafe files go into the system prompt every turn. A missing file is
  shown to Gemini as "no info yet" so it never invents details.
- Gemini's `cafe` tag is stored on both rows of a turn. `unknown` stays `unknown`.
- The chat's last 5 earlier messages (from Turso) are sent with each new message
  (`HISTORY_LIMIT` in `backend/llm.py`).
- Model: `gemini-3.5-flash-lite` (set in `.env`). Measured ~1-2 s per reply vs
  9-18 s and 503 "high demand" errors on `gemini-3.8-flash`.
- The user row keeps the time the message arrived, even though it is saved
  after the Gemini call (it needs Gemini's tag).

**Out of scope (later slices):** no-`?cafe=` flow where the bot asks which
cafe, web page, consent screen, safety check, voice, gender.

## Tasks

- [x] **T1 `[CODE]`** `backend/cafes.py`: `load_all_cafe_contexts()` returns all four cafes' info, labelled; a missing file becomes a "no info yet" note. Verify: `pytest tests/test_cafes.py`.
- [x] **T2 `[CODE]`** `backend/llm.py`: prompt from PRODUCT.md (all cafes + the cafe the link came from + tag rule); `get_reply` sends earlier messages as Gemini history. Verify: `pytest tests/test_llm.py`.
- [x] **T3 `[CODE]`** `backend/main.py`: accept any of the four cafes; load history; call LLM; save both rows with Gemini's tag; user row keeps its arrival time. Verify: `pytest` passes in full.
- [x] **T4 `[VERIFY]`** Real server: a 2-turn chat from `cafe=hashtag` that brings up Coffee Nation in turn 2. Show the bot remembers turn 1, and the rows are tagged hashtag then coffee_nation. Delete the test rows after.
- [ ] **T5 `[MANUAL]`** Write `cafes/coffee_nation.md`, `juice_press.md`, `barsha.md` (same format as hashtag.md, no invented details), then chat once per cafe and read the replies.
