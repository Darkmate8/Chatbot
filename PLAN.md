# Slice 3: crisis check before every reply

Slice 1 and Slice 2 are done (Slice 2 plan and decisions are in git history,
commits dbfdd2e and 2362b38). Slice 2 T5 is still open for you: write
`cafes/coffee_nation.md`, `juice_press.md`, `barsha.md`, then chat once per cafe.

**A student can:** send a message that mentions self-harm, suicide, abuse or
an acute crisis (including indirect phrasings) and get a fixed care reply
with helplines instead of the cafe persona. The research team can find those
turns through a `crisis` column.

**Decisions (2026-10-19):**
- A separate Gemini call classifies every user message before the persona
  reply. Its prompt lives in PRODUCT.md.
- Care reply: one fixed text from PRODUCT.md, never written by Gemini.
  Your team must replace `[CAMPUS COUNSELING TBD]` and sign off the wording.
- Fail safe: if the check errors, or the persona call returns no text
  (Gemini blocked it), the student gets the care reply and the turn is flagged.
- Flag: new `crisis` column (0/1) on both rows of the turn. Rows are stored
  like any other. No message text in logs.
- Crisis turns are tagged cafe `unknown` (no persona call, so no Gemini tag).

**Out of scope (later slices):** consent screen, web page, voice, gender.

## Tasks

- [x] **T1 `[CODE]`** PRODUCT.md: classifier prompt, care reply text, `crisis` column, the decisions above.
- [x] **T2 `[CODE]`** `backend/safety.py`: `is_crisis(message)`: separate Gemini call, JSON `{crisis}`; any error or bad output counts as crisis. Prompt and care reply match PRODUCT.md (test). Verify: `pytest tests/test_safety.py`.
- [x] **T3 `[CODE]`** `backend/safety.py`: `respond(history, message, cafe_context, entry_cafe)` returns `(reply, cafe, crisis)`: crisis → care reply; persona gives no text → care reply + flag; else the persona reply. Verify: `pytest tests/test_safety.py`.
- [x] **T4 `[CODE]`** `backend/main.py` uses `respond` and saves `crisis` on both rows. Verify: `pytest tests/test_main.py`.
- [x] **T5 `[YOU]`** Add the column in the Turso shell: `ALTER TABLE messages ADD COLUMN crisis INTEGER NOT NULL DEFAULT 0;`
- [x] **T6 `[CODE]`** `backend/db.py`: `insert_message(..., crisis=False)` stores it; `get_messages` returns it. Verify: `pytest` passes in full (needs T5).
- [x] **T7 `[VERIFY]`** Real server: 1 normal message, 3 crisis messages (1 direct, 2 indirect), 2 non-crisis messages with crisis-like words ("this exam is killing me", "the fries were to die for"). Show replies and `crisis` values; delete the test rows.
- [ ] **T8 `[MANUAL]`** Team fills in the campus counseling contact, signs off the care reply, and tests more phrasings before launch.
