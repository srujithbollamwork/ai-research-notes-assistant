# services/groq_utils.py
import os
import requests
from dotenv import load_dotenv
load_dotenv()

from groq import Groq, BadRequestError

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


def extract_message_content(resp) -> str:
    """
    Robustly extract the assistant content from a Groq chat completion response.
    Handles these possible shapes:
     - resp.choices[0].message is a dict-like -> {'content': '...'}
     - resp.choices[0].message is a ChatCompletionMessage object with .content attribute
     - resp.choices[0].message has .get('content')
     - resp.choices[0].message is nested
    Returns a stripped string ('' on failure).
    """
    try:
        choice = resp.choices[0]
    except Exception:
        return ""

    # Try to get message object
    msg = None
    try:
        msg = getattr(choice, "message", None)
    except Exception:
        msg = None

    # If no message attribute, attempt dict-style
    if msg is None:
        try:
            # many SDKs return dict-like choices
            if isinstance(choice, dict):
                m = choice.get("message") or choice.get("delta") or {}
                if isinstance(m, dict):
                    return (m.get("content") or "").strip()
                return str(m).strip()
            # fallback: stringify the choice
            return str(choice).strip()
        except Exception:
            return ""

    # If msg is dict-like
    try:
        if isinstance(msg, dict):
            return (msg.get("content") or "").strip()
    except Exception:
        pass

    # If msg has get(...)
    try:
        if hasattr(msg, "get"):
            maybe = msg.get("content", None)
            if isinstance(maybe, str):
                return maybe.strip()
            if isinstance(maybe, dict):
                return (maybe.get("content") or "").strip()
    except Exception:
        pass

    # If msg has attribute .content (ChatCompletionMessage)
    try:
        if hasattr(msg, "content"):
            c = msg.content
            if isinstance(c, str):
                return c.strip()
            if isinstance(c, dict):
                return (c.get("content") or "").strip()
            return str(c).strip()
    except Exception:
        pass

    # As a last resort try to stringify msg
    try:
        return str(msg).strip()
    except Exception:
        return ""


def call_chat_with_fallback(messages, model: str | None = None, **kwargs):
    """
    Call Groq chat.completions with preferred model.
    If it fails with BadRequestError (e.g., model decommissioned) try fallback model(s).
    Returns the raw resp object on success or raises the last exception.
    """
    preferred = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    fallbacks = []
    env_fb = os.getenv("GROQ_FALLBACK_MODEL")
    if env_fb:
        fallbacks.append(env_fb)
    default_fb = "llama-3.1-8b-instant"
    if default_fb not in fallbacks and preferred != default_fb:
        fallbacks.append(default_fb)

    last_exc = None
    try:
        return client.chat.completions.create(messages=messages, model=preferred, **kwargs)
    except BadRequestError as e:
        last_exc = e
        # try fallbacks
        for fb in fallbacks:
            try:
                return client.chat.completions.create(messages=messages, model=fb, **kwargs)
            except Exception as e2:
                last_exc = e2
        # nothing worked
        raise last_exc
    except Exception as e:
        raise e


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
