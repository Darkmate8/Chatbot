import json
import os

from google import genai
from google.genai import types

from backend.db import ALLOWED_CAFES

# Copied verbatim from PRODUCT.md, "System prompt and safety layer".
SYSTEM_PROMPT_TEMPLATE = """\
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
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "cafe": {"type": "string", "enum": sorted(ALLOWED_CAFES)},
    },
    "required": ["reply", "cafe"],
}


def build_system_prompt(cafe_context):
    # .replace, not .format: the template's JSON example contains literal braces.
    return SYSTEM_PROMPT_TEMPLATE.replace("{cafe_context}", cafe_context)


def get_reply(message, cafe_context, client=None):
    client = client or genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=os.environ["GEMINI_MODEL"],
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=build_system_prompt(cafe_context),
            response_mime_type="application/json",
            response_json_schema=RESPONSE_SCHEMA,
        ),
    )
    return parse_response(response.text)


def parse_response(text):
    try:
        data = json.loads(text)
        reply = data["reply"]
    except (json.JSONDecodeError, TypeError, KeyError):
        return text, "unknown"
    cafe = data.get("cafe")
    return reply, cafe if cafe in ALLOWED_CAFES else "unknown"
