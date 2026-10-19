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
    try:
        cafe_context = cafes.load_cafe_context(body.cafe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    chat_id = str(body.chat_id)
    db.insert_message(chat_id, "user", body.message, body.cafe)
    # Slice 1 stores the cafe from the request; Gemini's cafe tag is used in Slice 2.
    reply, _ = llm.get_reply(body.message, cafe_context)
    db.insert_message(chat_id, "bot", reply, body.cafe)
    return {"reply": reply}
