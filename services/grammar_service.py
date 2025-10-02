# services/grammar_service.py
import os
from dotenv import load_dotenv
load_dotenv()

import language_tool_python
from typing import Dict, Any, List

from services.groq_utils import call_chat_with_fallback, extract_message_content

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_tool = None
def _get_languagetool():
    global _tool
    if _tool is None:
        _tool = language_tool_python.LanguageTool('en-US')
    return _tool


def check_with_languagetool(text: str) -> List[Dict[str, Any]]:
    if not text.strip():
        return []
    tool = _get_languagetool()
    matches = tool.check(text)
    return [{"error": m.message, "suggestions": m.replacements} for m in matches]


def improve_with_groq(text: str, max_words: int = 300) -> str:
    if not text.strip():
        return "Error: No text provided."
    prompt = (
        f"Improve the following academic text for grammar, readability, and clarity. "
        f"Do not change the meaning. Limit to about {max_words} words.\n\n{text}"
    )
    resp = call_chat_with_fallback([{"role": "user", "content": prompt}], model=MODEL)
    return extract_message_content(resp)


def grammar_check_report(text: str) -> Dict[str, Any]:
    if not text.strip():
        return {"error": "Empty text provided."}
    issues = check_with_languagetool(text)
    improved = improve_with_groq(text)
    return {"original": text, "grammar_issues": issues, "improved_text": improved}
