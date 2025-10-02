# services/study_service.py
import os
import re
from dotenv import load_dotenv
load_dotenv()

from services.groq_utils import call_chat_with_fallback, extract_message_content

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _parse_flashcards_from_text(raw: str):
    """
    Parse Q/A pairs from model output.
    """
    if not raw:
        return []

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    qa = []
    q = None
    for line in lines:
        m_q = re.match(r'^(?:Q\d*[:\.\s-]*)(.*)', line, flags=re.I)
        m_a = re.match(r'^(?:A\d*[:\.\s-]*)(.*)', line, flags=re.I)
        if m_q and m_q.group(1).strip():
            q = m_q.group(1).strip()
            continue
        if m_a and m_a.group(1).strip() and q:
            a = m_a.group(1).strip()
            qa.append({"question": q, "answer": a})
            q = None
            continue
        if " - " in line or " — " in line:
            parts = re.split(r'\s[-—]\s', line, maxsplit=1)
            if len(parts) == 2:
                qa.append({"question": parts[0].strip(), "answer": parts[1].strip()})
                q = None
                continue
    return qa


def generate_flashcards(text: str, num_cards: int = 5):
    if not text.strip():
        return [{"error": "Empty text provided"}]
    prompt = (
        f"Create {num_cards} concise flashcards (question and short answer pairs) "
        f"from the academic text below. Number them.\n\n{text}"
    )
    resp = call_chat_with_fallback([{"role": "user", "content": prompt}], model=MODEL)
    raw = extract_message_content(resp)
    qa = _parse_flashcards_from_text(raw)
    if qa:
        return qa[:num_cards]
    return [{"question": "Main idea", "answer": raw.strip()}] if raw else [{"error": "Could not generate flashcards"}]


def generate_practice_questions(text: str, num_questions: int = 5):
    if not text.strip():
        return ["Error: Empty text provided"]
    prompt = (
        f"Generate {num_questions} open-ended practice questions based on the following academic text. "
        f"Do not include answers.\n\n{text}"
    )
    resp = call_chat_with_fallback([{"role": "user", "content": prompt}], model=MODEL)
    raw = extract_message_content(resp)
    lines = [re.sub(r'^\d+[\).\s-]*', '', l).strip() for l in raw.splitlines() if l.strip()]
    return lines[:num_questions] if lines else [raw]
