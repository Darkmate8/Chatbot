from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import UUID4, BaseModel

from backend import cafes, db, llm

load_dotenv()

app = FastAPI()


class ChatRequest(BaseModel):
    chat_id: UUID4  # random, from crypto.randomUUID() in the browser; anything else is rejected
    cafe: str
    message: str


# The handler deliberately takes no Request object, so it cannot read the
# client IP, user agent or any other header.
@app.post("/chat")
def chat(body: ChatRequest):
    if body.cafe not in cafes.CAFES:
        raise HTTPException(status_code=400, detail=f"Unknown cafe: {body.cafe!r}. Expected one of {sorted(cafes.CAFES)}")

    received_at = datetime.now(timezone.utc)
    chat_id = str(body.chat_id)
    history = db.get_messages(chat_id)
    reply, cafe_tag = llm.get_reply(history, body.message, cafes.load_all_cafe_contexts(), body.cafe)
    # The user row is saved after the Gemini call because it needs Gemini's cafe tag,
    # but it keeps the time the message arrived.
    db.insert_message(chat_id, "user", body.message, cafe_tag, now=received_at)
    db.insert_message(chat_id, "bot", reply, cafe_tag)
    return {"reply": reply}
