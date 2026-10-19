from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import UUID4, BaseModel

from backend import cafes, db, safety

load_dotenv()

# Must match the consent text the page shows (see PRODUCT.md). Bump on any wording change.
CONSENT_VERSION = "v1-draft"

app = FastAPI()


class ChatRequest(BaseModel):
    chat_id: UUID4  # random, from crypto.randomUUID() in the browser; anything else is rejected
    cafe: str
    message: str
    consent_version: str


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
    db.insert_message(chat_id, "user", body.message, cafe_tag, now=received_at, crisis=crisis, consent_version=CONSENT_VERSION)
    db.insert_message(chat_id, "bot", reply, cafe_tag, crisis=crisis, consent_version=CONSENT_VERSION)
    return {"reply": reply}


# Mounted last so /chat wins; serves frontend/index.html at "/".
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
