import json
import os

from google import genai
from google.genai import types

from backend import llm

# Copied verbatim from PRODUCT.md, "Crisis classifier prompt".
CLASSIFIER_PROMPT = """\
You check one message from a university student who is chatting with
a cafe chatbot. Decide whether it mentions or hints at self-harm,
suicide, abuse, or an acute crisis. Count indirect phrasings, such as
"I don't want to be here anymore" or "nobody would notice if I
disappeared". Everyday stress, tiredness, figures of speech ("this
exam is killing me"), and complaints about food or noise are not a
crisis.

Output format (JSON): {"crisis": true or false}
"""

# Copied verbatim from PRODUCT.md, "Care reply". Fixed text, never written by Gemini.
CARE_REPLY = (
    "Thank you for telling me. It sounds like you are going through something really hard, "
    "and you deserve support from a real person. You can call Tele-MANAS for free, any time, "
    "at 14416. On campus, you can reach [CAMPUS COUNSELING TBD]. "
    "If you are in immediate danger, please call 112."
)

CLASSIFIER_SCHEMA = {
    "type": "object",
    "properties": {"crisis": {"type": "boolean"}},
    "required": ["crisis"],
}


def is_crisis(message, client=None):
    # Fail safe: any error or unexpected output counts as a crisis, so a broken
    # check never lets a crisis message through to the cafe persona.
    try:
        client = client or genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model=os.environ["GEMINI_MODEL"],
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=CLASSIFIER_PROMPT,
                response_mime_type="application/json",
                response_json_schema=CLASSIFIER_SCHEMA,
            ),
        )
        crisis = json.loads(response.text)["crisis"]
    except Exception:
        return True
    return crisis if isinstance(crisis, bool) else True


def respond(history, message, cafe_context, entry_cafe):
    """Returns (reply, cafe, crisis) for one turn."""
    if is_crisis(message):
        return CARE_REPLY, "unknown", True
    reply, cafe = llm.get_reply(history, message, cafe_context, entry_cafe)
    if not reply:
        # Gemini sent no text (usually its own safety filter blocked the reply).
        return CARE_REPLY, "unknown", True
    return reply, cafe, False
