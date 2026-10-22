# Slice 6: voice to text

Slices 1-5 are done (plans in git history; Slice 5 is commit dcbe8b0). The
pilot at Hashtag ran.

**A student can:** tap the mic, speak, see their words appear in the text
box, fix them if needed, and send them like a typed message.

**Decisions (2026-10-21):**
- Gender estimation is split out into Slice 7. It needs its own library,
  consent wording and IRB check; voice to text works without it.
- Transcription runs on Gemini (same paid-tier key), not faster-whisper. The
  Render free instance (about 512 MB RAM) is too small for faster-whisper's
  small model. Paid-tier Gemini does not use content to improve Google
  products, but Google keeps prompts (now including audio) for a limited
  period for abuse detection only. Tell the IRB / data officer.
- The transcript fills the text box; the student edits and presses Send. They
  see and control what is stored (transcription errors, names said aloud).
- Transcribe word for word in the language spoken (Hindi-English mixing
  included), no translation: the emotion dataset needs the student's own words.
- `POST /transcribe` takes the raw audio as the request body, held in memory
  only. Not a multipart upload: FastAPI spools uploads over 1 MB to a temp
  file on disk. The handler takes no `Request` object (same as `/chat`).
- Limits: recording stops at 60 seconds; the server rejects bodies over 2 MB
  and audio types not on an allowlist, before calling Gemini.
- `input_mode` (`text` or `voice`) is saved on the user row; the bot row is
  always `text`. Editing a transcript before sending keeps it `voice`.
- The crisis check runs on the transcript through `/chat`, unchanged.
- Consent goes to `v2-draft` with one new line about recordings.

**Out of scope (later slices):** gender from voice (Slice 7), automatic
60-day deletion.

## Tasks

- [x] **T1 `[CODE]`** PRODUCT.md: speech-to-text decision, close that open question, architecture diagram, consent `v2-draft` line, roadmap (Slice 6 voice, Slice 7 gender).
- [x] **T2 `[VERIFY]`** Check the Turso `messages` table has an `input_mode` column (it was made by hand; no code uses it yet). If it is missing, stop and ask.
- [x] **T3 `[CODE]`** `db.insert_message` takes `input_mode` (default `text`, only `text`/`voice` allowed). Verify: `pytest tests/test_db.py`.
- [x] **T4 `[CODE]`** `/chat` accepts `input_mode`; the user row stores it, the bot row stores `text`. Verify: `pytest tests/test_main.py`.
- [x] **T5 `[CODE]`** `llm.transcribe(audio, mime_type)` sends the clip to Gemini with the transcription prompt and returns the text (empty if no speech). Check the google-genai docs for passing audio bytes. Verify: `pytest tests/test_llm.py`.
- [x] **T6 `[CODE]`** `POST /transcribe`: raw body, 2 MB cap, audio-type allowlist, returns `{"text": ...}`; a Gemini error returns a friendly 502. Never logs audio or text. Verify: `pytest tests/test_main.py`.
- [x] **T7 `[CODE]`** Consent `v2-draft`: `CONSENT_VERSION` and the page's consent text, with the new line. Verify: `pytest`.
- [x] **T8 `[CODE]`** Page: mic button, record with the browser's MediaRecorder, stop at 60 s, "Listening…" while transcribing, fill the text box, send `input_mode`. Clear messages for blocked mic or no speech. Verify: `pytest tests/test_frontend.py`.
- [ ] **T9 `[VERIFY]`** Local run with real Gemini in desktop Chrome, then push; on the live site, record on phone Chrome and Safari (Safari records MP4, not WebM). A test row has `input_mode = voice` and `consent_version = v2-draft`; delete test rows.
- [ ] **T10 `[MANUAL]`** Team sign-off on the new consent line.
