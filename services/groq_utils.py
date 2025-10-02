# services/groq_utils.py
import os
import requests
from dotenv import load_dotenv
load_dotenv()

from groq import Groq, BadRequestError, RateLimitError, APIError

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


def extract_message_content(resp) -> str:
    """
    Robustly extract the assistant content from a Groq chat completion response.
    Handles multiple response shapes.
    Returns a stripped string ('' on failure).
    """
    try:
        choice = resp.choices[0]
    except Exception:
        return ""

    msg = getattr(choice, "message", None)

    # If dict-like choice
    if msg is None and isinstance(choice, dict):
        m = choice.get("message") or choice.get("delta") or {}
        if isinstance(m, dict):
            return (m.get("content") or "").strip()
        return str(m).strip()

    # If dict-like message
    if isinstance(msg, dict):
        return (msg.get("content") or "").strip()

    # If message supports get()
    if hasattr(msg, "get"):
        maybe = msg.get("content", None)
        if isinstance(maybe, str):
            return maybe.strip()
        if isinstance(maybe, dict):
            return (maybe.get("content") or "").strip()

    # If message has .content
    if hasattr(msg, "content"):
        c = msg.content
        if isinstance(c, str):
            return c.strip()
        if isinstance(c, dict):
            return (c.get("content") or "").strip()
        return str(c).strip()

    try:
        return str(msg).strip()
    except Exception:
        return ""


def call_chat_with_fallback(messages, model: str | None = None, **kwargs):
    """
    Call Groq chat.completions with preferred model.
    Handles BadRequestError (decommissioned model),
    RateLimitError (quota exceeded), and generic API errors gracefully.
    """
    preferred = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    fallbacks = []
    env_fb = os.getenv("GROQ_FALLBACK_MODEL")
    if env_fb:
        fallbacks.append(env_fb)
    default_fb = "llama-3.1-8b-instant"
    if default_fb not in fallbacks and preferred != default_fb:
        fallbacks.append(default_fb)

    try:
        return client.chat.completions.create(messages=messages, model=preferred, **kwargs)

    except BadRequestError as e:
        # Try fallback models
        for fb in fallbacks:
            try:
                return client.chat.completions.create(messages=messages, model=fb, **kwargs)
            except Exception:
                continue
        # Nothing worked
        return {"choices": [{"message": {"content": f"⚠️ Model error: {str(e)}"}}]}

    except RateLimitError:
        return {"choices": [{"message": {"content": "⚠️ Rate limit exceeded. Please try again later."}}]}

    except APIError as e:
        return {"choices": [{"message": {"content": f"⚠️ API error: {str(e)}"}}]}

    except Exception as e:
        return {"choices": [{"message": {"content": f"⚠️ Unexpected error: {str(e)}"}}]}


def list_groq_models():
    """
    Optional: list models available to your API key (returns JSON).
    """
    if not GROQ_API_KEY:
        return []
    resp = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
    )
    resp.raise_for_status()
    return resp.json()
