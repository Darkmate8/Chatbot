# Slice 4: consent screen and chat page

Slices 1-3 are done (plans in git history; Slice 3 is commit 55f2937).
Still open for you: Slice 2 T5 (three cafe files) and Slice 3 T8 (campus
counseling contact + care reply sign-off).

**A student can:** open `/?cafe=hashtag` on their phone, read a consent
screen, agree, and chat with the bot in a simple chat page. Without `?cafe=`
the bot's greeting asks which cafe they mean. Every stored row carries the
consent version the student agreed to.

**Decisions (2026-10-19):**
- Plain HTML/CSS/JS in `frontend/`, served by FastAPI at `/`. No build step,
  no third-party requests at all (no CDN, fonts or analytics), since each one
  would send the student's IP to another company.
- `chat_id` is made with `crypto.randomUUID()` per page load and kept only in
  memory: a refresh starts a new anonymous chat.
- Consent text is drafted by Claude in PRODUCT.md as version `v1-draft`; the
  team must sign it off and fill the placeholders. The page and PRODUCT.md
  are kept identical by a test. Voice wording is added in Slice 6.
- `/chat` requires `consent_version` to equal the current version, and saves
  it on both rows. A page with stale consent text gets an error.
- No `?cafe=` (or an unrecognised value): entry cafe is `unknown`. The fixed
  greeting asks which cafe; Gemini's tag picks it up from the answer. The
  greeting is shown by the page and not stored.

**Out of scope (later slices):** QR codes and pilot (Slice 5), voice (Slice 6).

## Tasks

- [x] **T1 `[CODE]`** PRODUCT.md: consent text `v1-draft`, the two greetings, the decisions above.
- [x] **T2 `[CODE]`** `backend/db.py`: `insert_message(..., consent_version=None)` stores it. Verify: `pytest tests/test_db.py`.
- [x] **T3 `[CODE]`** `backend/main.py`: `/chat` takes `consent_version` (must equal `CONSENT_VERSION`) and saves it on both rows; entry cafe `unknown` is accepted. Verify: `pytest tests/test_main.py`.
- [x] **T4 `[CODE]`** `frontend/` page served at `/`: consent screen, then chat. Tests: the page contains the PRODUCT.md consent text and version, and every cafe. Verify: `pytest` passes in full.
- [x] **T5 `[VERIFY]`** Real server: load `/` and `/?cafe=hashtag`, send messages exactly as the page does, show rows with `consent_version = v1-draft`; delete test rows.
- [ ] **T6 `[MANUAL]`** Open the page on your phone, click through consent and chat. Team signs off the consent text.
