# Cafe Chatbot: Product Brief

Last updated: 2026-10-18

## Goal and decisions

An anonymous chatbot that talks with FLAME University students about one of
four campus cafes and records the conversations, with consent, so the
research team can later train an emotion-detection model (Hashtag chatbot
research project, VR emotion-detecting AI). The bot's only job is to be a
warm listener that gets students talking naturally; the product is the data.

The four cafes: Hashtag, Coffee Nation (CN), Juice Press (JP), Barsha.

| Decision | Choice |
| --- | --- |
| Bot persona | Warm, non-judgmental, open-ended follow-ups, no advice, no engagement bait |
| LLM | Gemini API, paid tier only (free tier can use content to improve Google products) |
| Speech-to-text | Not Parakeet by default (needs a GPU). Preferred: faster-whisper (small model) inside the Python backend. Voice comes after text, in a later slice |
| Database | Turso |
| Gender | Inferred from voice with a Python library; noisy and accepted. Null for text users |
| Identifiers | No names, emails, accounts, IPs, or audio stored |
| Cafe detection | `?cafe=` URL/QR parameter first; bot asks in chat if missing; Gemini tags the cafe on every reply |
| Cafe knowledge | One short text file per cafe injected into the system prompt. No full RAG unless the content outgrows the prompt |
| Safety | Separate crisis check on every user message, before the persona reply |
| Ethics | IRB approval is in place |

## Architecture

```
Student browser --> Backend API (FastAPI) --> Gemini API (reply + cafe tag)
                         |   |  \--> Safety check (crisis -> care reply)
                         |   \-----> Turso DB (chats, cafe, gender)
                         \--> Cafe context files (menu, features, vibe)
                         \--> faster-whisper + gender library (voice only; audio deleted)
```

Cafe detection, in order:

1. A QR code or URL parameter (for example `?cafe=hashtag`) sets the cafe silently.
2. With no parameter, the bot's first message asks which cafe the student means. No button or dropdown.
3. Gemini returns a structured `cafe` tag on every turn, limited to the four cafes or `unknown`.
4. The cafe is stored per message, not per chat, because one chat can compare two cafes.

## Database schema (Turso)

One table. One row per message. A random `chat_id` made in the browser groups
rows into conversations; it is not linked to a name, email, device or IP.

| Column | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| chat_id | text | Random, made in the browser per visit |
| role | text | `user` or `bot` |
| content | text | Message text (transcript if from voice) |
| created_at | text | UTC timestamp |
| local_hour | integer | 0 to 23 in IST, for time-of-day analysis |
| cafe | text | `hashtag`, `coffee_nation`, `juice_press`, `barsha`, or `unknown` |
| input_mode | text | `text` or `voice` |
| gender | text | Estimated from voice; null for text users |
| gender_source | text | `inferred_voice` or null, so noisy labels can be filtered later |
| consent_version | text | Which consent wording the student saw |

Because nothing links a chat to a person, individual chats cannot be deleted
on request. The consent screen must say so.

## System prompt and safety layer

The bot is a warm listener, not a salesperson: it reflects what the student
said and asks one open question, with no pressure to share more.

```
You are a friendly AI companion chatting with students about their
experiences at cafes at FLAME University. You are an AI, and you say
so if asked.

Cafe info for the cafe being discussed:
{cafe_context}

Style:
- Warm, curious and non-judgmental. Never criticize, correct or lecture.
- Reflect back what the student said in a few words, then ask ONE
  open-ended follow-up about how it felt or what it meant to them.
- Do not give advice or fix problems unless the student asks.
- Keep replies to 2 or 3 short sentences.
- Use the cafe info to sound informed (menu items, books, seating),
  but never invent details that are not in it.
- Do not push anyone to share more than they want to. If they seem
  done, let them be done.

Output format (JSON): {"reply": "...", "cafe": one of
["hashtag", "coffee_nation", "juice_press", "barsha", "unknown"]}
```

Safety layer: run a separate, cheap classifier call on every user message
before the persona reply. The "don't advise, just support" persona conflicts
with how a crisis should be handled, so the system prompt alone is not enough.

- If the message mentions self-harm, suicide, abuse or acute crisis, skip the cafe persona and reply with care.
- Share Tele-MANAS (14416) and the campus counseling contact (to be filled in by the team).
- Flag the message in the logs so the research team knows a crisis response was triggered. Do not continue the cafe conversation in the same turn.
- Test with made-up messages before launch, including indirect phrasings.

## Privacy, consent and IRB checklist

- [ ] Gemini on the paid tier; its data-use terms checked against the IRB protocol
- [ ] IRB protocol covers voice-inferred gender and the random `chat_id`
- [ ] Retention: every row is deleted 60 days after its `created_at` (decided 2026-10-19). Turso backups keep deleted rows for up to the plan's restore window on top of that. Automatic deletion is not built yet; the consent screen must state the 60 days.
- [ ] Host logging checked: services like Vercel and Cloudflare record IPs by default, which conflicts with "no identifiers stored"
- [ ] One consent screen, shown once, before the first message: it is an AI, chats are recorded anonymously for research, voice is analysed for gender and the audio is discarded, a chat cannot be deleted later because nothing links it to a person
- [ ] Audio deleted immediately after transcription and gender estimation; never written to disk or the database
- [ ] DPDP Act 2023 considered; confirm with the professor whether the university's data officer must sign off
- [ ] `consent_version` stored on every row

## Roadmap (vertical slices)

Each slice is something a student can actually do. Details for the current
slice live in PLAN.md.

| Slice | A student can... |
| --- | --- |
| 1 | Send one message about Hashtag and get a Gemini reply, both saved in Turso |
| 2 | Use any of the four cafes through `?cafe=`, with context files and the per-message cafe tag |
| 3 | Trigger the care reply on crisis messages |
| 4 | See the consent screen and use the chat page |
| 5 | Scan a QR code in a real cafe (pilot with 5 to 10 students) |
| 6 | Talk by voice, with gender estimated and audio deleted |

## Open questions

- Who writes the four cafe context files (Hashtag, Coffee Nation, Juice Press, Barsha), and by when?
- Where will the site and backend be hosted, given free-tier limits and default IP logging?
- Where will speech-to-text run when voice is added?
- Will the site be reachable only through cafe QR codes, or also as an open URL? If open, the bot asks which cafe in its first message.
