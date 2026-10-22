from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import UUID4, BaseModel, Field

from backend import cafes, db, llm, safety

load_dotenv()

# Must match the consent text the page shows (see PRODUCT.md). Bump on any wording change.
CONSENT_VERSION = "v2-draft"

# The site is public, so cap message size to stop anyone running up the Gemini bill.
# frontend/index.html has the same maxlength (a test keeps them equal).
MAX_MESSAGE_LENGTH = 2000

# A 60-second recording is well under 1 MB; the cap stops anyone sending huge files to Gemini.
MAX_AUDIO_BYTES = 2_000_000
# What MediaRecorder makes: webm (Chrome, Firefox), mp4 (Safari), ogg (older Firefox).
ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/mp4", "audio/ogg"}

app = FastAPI()


class ChatRequest(BaseModel):
    chat_id: UUID4  # random, from crypto.randomUUID() in the browser; anything else is rejected
    cafe: str
    message: str = Field(max_length=MAX_MESSAGE_LENGTH)
    consent_version: str
    input_mode: Literal["text", "voice"] = "text"  # "voice" if the text came from /transcribe, even if edited


# The handler deliberately takes no Request object, so it cannot read the
# client IP, user agent or any other header.
@app.post("/chat")
def chat(body: ChatRequest):
    # "unknown" means the link had no ?cafe=; the greeting asks which cafe.
    if body.cafe not in cafes.CAFES and body.cafe != "unknown":
        raise HTTPException(status_code=400, detail=f"Unknown cafe: {body.cafe!r}. Expected one of {sorted(cafes.CAFES)} or 'unknown'")
    if body.consent_version != CONSENT_VERSION:
        raise HTTPException(status_code=400, detail="Consent version is out of date. Please reload the page.")

    received_at = datetime.now(timezone.utc)
    chat_id = str(body.chat_id)
    history = db.get_messages(chat_id)
    reply, cafe_tag, crisis = safety.respond(history, body.message, cafes.load_all_cafe_contexts(), body.cafe)
    # The user row is saved after the Gemini call because it needs Gemini's cafe tag,
    # but it keeps the time the message arrived.
    db.insert_message(chat_id, "user", body.message, cafe_tag, now=received_at, crisis=crisis, consent_version=CONSENT_VERSION, input_mode=body.input_mode)
    db.insert_message(chat_id, "bot", reply, cafe_tag, crisis=crisis, consent_version=CONSENT_VERSION)
    return {"reply": reply}


async def read_audio(request: Request):
    # Reads the raw body in chunks and stops past the cap, so a huge upload never
    # fills memory. Kept in memory only: never written to disk. This dependency
    # reads nothing from the request except the body.
    audio = bytearray()
    async for chunk in request.stream():
        audio += chunk
        if len(audio) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Recording is too long.")
    return bytes(audio)


@app.post("/transcribe")
def transcribe(content_type: str = Header(), audio: bytes = Depends(read_audio)):
    # "audio/webm;codecs=opus" -> "audio/webm"
    mime_type = content_type.split(";")[0].strip().lower()
    if mime_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported audio type. Expected one of {sorted(ALLOWED_AUDIO_TYPES)}")
    if not audio:
        raise HTTPException(status_code=400, detail="Recording is empty.")
    try:
        text = llm.transcribe(audio, mime_type)
    except Exception:
        # Not logged: the error is about Gemini, and logging risks leaking content.
        raise HTTPException(status_code=502, detail="Sorry, I couldn't hear that. Please try again or type instead.") from None
    return {"text": text[:MAX_MESSAGE_LENGTH]}


# Mounted last so /chat and /transcribe win; serves frontend/index.html at "/".
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
