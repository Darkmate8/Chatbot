# Slice 5: live on Render, QR codes, pilot

Slices 1-4 are done (plans in git history; Slice 4 is commit 80fc097).
Still open for you: Slice 2 T5 (three cafe files), Slice 3 T8 (campus
counseling contact + care reply sign-off), Slice 4 T6 (consent sign-off +
research team contact).

**A student can:** scan a QR code at Hashtag with their phone, land on the
live site with the cafe already set, agree to the consent screen and chat.

**Decisions (2026-10-21):**
- Host: Render, on a Hobby workspace. Render only makes per-request HTTP logs
  on Pro workspaces and up, so we never get a log of visitor IPs. Railway was
  ruled out: it logs every visitor IP for 90 days and it cannot be turned
  off. Like every host, Render's network still sees IPs to deliver the page;
  what we control is that neither our app nor our logs keep them.
- Region `singapore` (closest to Pune). Python pinned by `.python-version`.
- Config lives in `render.yaml` (a Render "Blueprint"), so the start command,
  including `--no-access-log`, is in git and checked by a test, not typed
  into a dashboard.
- Instance `plan: free` (Render's default is paid, so it is set explicitly).
  A free instance sleeps after about 15 idle minutes and the first visit then
  takes about a minute. Before the pilot, either switch to the smallest paid
  instance in the dashboard (about $7/month) or open the site yourself just
  before students scan.
- The site is public, so anyone could send huge messages that cost Gemini
  money. `/chat` rejects messages over 2000 characters, and the text box
  stops at 2000.
- QR codes are made by our own script as plain SVG files. Many free QR
  websites make "dynamic" codes that send students through their own
  redirect server, which logs the student's IP.
- Pilot runs at Hashtag only until the other three cafe files exist; the bot
  knows nothing about cafes without a file.

**Out of scope (later slices):** voice (Slice 6), automatic 60-day deletion.

## Tasks

- [x] **T1 `[CODE]`** PRODUCT.md: record the hosting decision and close that open question.
- [x] **T2 `[CODE]`** `/chat` rejects messages over 2000 characters; the text box has `maxlength`. Verify: `pytest tests/test_main.py tests/test_frontend.py`.
- [x] **T3 `[CODE]`** `render.yaml` + `.python-version`. Test: the start command binds `0.0.0.0:$PORT` and keeps `--no-access-log`; plan is `free`; secrets are `sync: false`. Verify: `pytest`.
- [x] **T4 `[CODE]`** `scripts/make_qr.py <site-url>` writes `qr/<cafe>.svg` for each cafe (needs `pip install -r requirements-dev.txt`). Test: the encoded links are `<site-url>/?cafe=<slug>`.
- [ ] **T5 `[CODE]`** Push to GitHub (the repo is public; history checked for secrets on 2026-10-21, none found).
- [ ] **T6 `[MANUAL]`** You, about 5 minutes: sign up at render.com with GitHub (Hobby workspace), New > Blueprint > pick this repo, paste the four values from your `.env` when asked, Apply. Send me the `https://....onrender.com` link.
- [ ] **T7 `[VERIFY]`** Live site: page loads, a test chat is saved with `consent_version = v1-draft`, test rows deleted. You check Render's Logs tab shows no IP addresses.
- [ ] **T8 `[CODE]`** Make the QR codes with the live link and commit them.
- [ ] **T9 `[MANUAL]`** Before any real student: fill the three placeholders and get team sign-off (Slice 3 T8, Slice 4 T6), set a Gemini budget alert in Google Cloud, decide free vs paid instance. Then the pilot: 5 to 10 students at Hashtag.
