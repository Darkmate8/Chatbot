# Cafe Chatbot

Anonymous research chatbot. Students chat about one of four FLAME cafes; the
chats are stored to train an emotion-detection model later. Full context
(goal, schema, prompt, privacy checklist) is in PRODUCT.md. Current work is
in PLAN.md. Do not duplicate either file here.

## Commands (update when they change)
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt` (the server itself only installs requirements.txt)
- Run: `uvicorn backend.main:app --reload --no-access-log` (the access log prints client IPs; never drop this flag)
- Test: `pytest`

## Hard rules (never break; if a change would, stop and ask)
- Never store names, emails, IP addresses, user agents, device IDs, or audio.
  The only grouping key is `chat_id`, a random value made in the browser.
- Never print or log message content, API keys, or tokens.
- Secrets live only in `.env`. `.env` is in `.gitignore` and is never committed.
- Allowed cafe values: `hashtag`, `coffee_nation`, `juice_press`, `barsha`, `unknown`.
- Use only a paid-tier Gemini key (the free tier may use content to improve
  Google products). The model name comes from `GEMINI_MODEL` in `.env`; do not
  hardcode it.
- Bot persona: warm, non-judgmental, reflects what the student said, asks ONE
  open-ended follow-up, gives no advice, never pushes for more. It says it is
  an AI if asked. No engagement bait.

## How to work
- One vertical slice at a time, exactly as written in PLAN.md. Do not build
  ahead into later slices.
- Tests first: show the failing test, then make it pass.
- After each task, show me the diff and wait before starting the next one.
- I am a beginner. For any non-obvious choice, explain it in 2 or 3 sentences.
- If the task matches settled standard practice, just do it. If you would
  deviate from standard practice, flag it before implementing.
- Prefer the simplest solution for the CURRENT task. If a simple choice would
  need reworking for a requirement already visible in PRODUCT.md, stop and ask.
- For library APIs (Turso client, Gemini SDK), check the current official docs
  instead of relying on memory.

## Mistakes ledger
When I correct you, append a bounded rule here (what to do, when, and when to
ask instead).

- (empty)
