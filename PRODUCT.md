# Cafe Chatbot: Product Brief

Last updated: 2026-10-19

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
| Hosting | Render, Hobby workspace (no per-request HTTP logs on that plan), region Singapore, config in `render.yaml`. Railway ruled out: it logs visitor IPs for 90 days with no opt-out |
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
| crisis | integer | 1 if the crisis check fired for this turn (set on both rows), else 0 |

Because nothing links a chat to a person, individual chats cannot be deleted
on request. The consent screen must say so.

## System prompt and safety layer

The bot is a warm listener, not a salesperson: it reflects what the student
said and asks one open question, with no pressure to share more.

```
You are a friendly AI companion chatting with students about their
experiences at cafes at FLAME University. You are an AI, and you say
so if asked.

The student opened this chat from the link for: {entry_cafe}

Info for each cafe (use only this):
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
Set "cafe" to the cafe the student's latest message is about, using
the conversation so far. Use "unknown" if you cannot tell.
```

Safety layer: run a separate, cheap classifier call on every user message
before the persona reply. The "don't advise, just support" persona conflicts
with how a crisis should be handled, so the system prompt alone is not enough.

- If the message mentions self-harm, suicide, abuse or acute crisis, skip the cafe persona and reply with care.
- Share Tele-MANAS (14416) and the campus counseling contact (to be filled in by the team).
- Flag the turn with `crisis = 1` on both rows so the research team knows a crisis response was triggered. Never put message text in logs. Do not continue the cafe conversation in the same turn.
- Crisis turns are stored like other turns, with cafe `unknown`.
- Fail safe: if the classifier call errors or returns bad output, or the persona call returns no text, send the care reply and flag the turn.
- Test with made-up messages before launch, including indirect phrasings.

### Crisis classifier prompt

```
You check one message from a university student who is chatting with
a cafe chatbot. Decide whether it mentions or hints at self-harm,
suicide, abuse, or an acute crisis. Count indirect phrasings, such as
"I don't want to be here anymore" or "nobody would notice if I
disappeared". Everyday stress, tiredness, figures of speech ("this
exam is killing me"), and complaints about food or noise are not a
crisis.

Output format (JSON): {"crisis": true or false}
```

### Care reply

Fixed text, never written by Gemini. The team must replace the placeholder
and sign off the wording before launch.

```
Thank you for telling me. It sounds like you are going through something really hard, and you deserve support from a real person. You can call Tele-MANAS for free, any time, at 14416. On campus, you can reach [CAMPUS COUNSELING TBD]. If you are in immediate danger, please call 112.
```

## Consent screen and greetings

Shown once per visit, before the first message. Current version: `v1-draft`
(drafted by Claude on 2026-10-19 from the checklist below). The team must
fill the placeholder and sign off the wording before launch; any wording
change needs a new version. Voice wording is added in Slice 6.

Consent text, one paragraph per line:

```
This is an AI chatbot, not a person. It is part of a FLAME University research project about how students feel about campus cafes.
Your messages are saved anonymously for research. We do not collect your name, email, phone number, IP address or device details.
Please do not type your name or anything else that could identify you or someone else.
Your messages are sent to Google's Gemini AI to write the replies. Google does not use them to improve its products.
Because nothing links a chat to you, we cannot find or delete your chat later. All chats are deleted 60 days after they are written.
If a message suggests you might be in crisis, the bot will share helpline numbers, and the research team will see that this happened.
Taking part is voluntary. You can stop at any time by closing this page.
Questions about the study: [RESEARCH TEAM CONTACT TBD].
```

Buttons: "I agree, start chatting" and "No thanks". "No thanks" shows: "No
problem. You can close this page." Nothing is sent or stored.

Greeting (fixed, shown by the page, not stored), with and without `?cafe=`:

```
Hi! I'm an AI, here to hear about your time at {cafe_name}. How has it been?
Hi! I'm an AI, here to hear about the cafes at FLAME. Which cafe are you at, or thinking about?
```

## Privacy, consent and IRB checklist

- [ ] Gemini on the paid tier; its data-use terms checked against the IRB protocol
- [ ] IRB protocol covers voice-inferred gender and the random `chat_id`
- [ ] Retention: every row is deleted 60 days after its `created_at` (decided 2026-10-19). Turso backups keep deleted rows for up to the plan's restore window on top of that. Automatic deletion is not built yet; the consent screen must state the 60 days.
- [ ] Host logging checked: services like Vercel and Cloudflare record IPs by default, which conflicts with "no identifiers stored". Render chosen (2026-10-21): Hobby workspaces get no HTTP request logs; confirm on the live site that the Logs tab shows no IPs
- [ ] One consent screen, shown once, before the first message: it is an AI, chats are recorded anonymously for research, voice is analysed for gender and the audio is discarded, a chat cannot be deleted later because nothing links it to a person
- [ ] Audio deleted immediately after transcription and gender estimation; never written to disk or the database
- [ ] DPDP Act 2023 considered; confirm with the professor whether the university's data officer must sign off
- [x] `consent_version` stored on every row (from Slice 4)

## Roadmap (vertical slices)

Each slice is something a student can actually do. Details for the current
slice live in PLAN.md.

| Slice | A student can... |
| --- | --- |
| 1 | Send one message about Hashtag and get a Gemini reply, both saved in Turso |
| 2 | Use any of the four cafes through `?cafe=`, with context files, the per-message cafe tag, and a bot that remembers earlier messages in the chat |
| 3 | Trigger the care reply on crisis messages |
| 4 | See the consent screen and use the chat page |
| 5 | Scan a QR code in a real cafe (pilot with 5 to 10 students) |
| 6 | Talk by voice, with gender estimated and audio deleted |

## Open questions

- Who writes the four cafe context files (Hashtag, Coffee Nation, Juice Press, Barsha), and by when?
- Where will speech-to-text run when voice is added?
- Will the site be reachable only through cafe QR codes, or also as an open URL? If open, the bot asks which cafe in its first message.
