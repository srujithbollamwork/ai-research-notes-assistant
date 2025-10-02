# services/ai_service.py
import os
from dotenv import load_dotenv
load_dotenv()

from services.groq_utils import call_chat_with_fallback, extract_message_content

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def generate_summary(text: str) -> str:
    if not text or not text.strip():
        return "Error: No text supplied for summarization."
    prompt = (
        "Summarize the following text in a concise academic summary (3-6 sentences). "
        "Do not invent facts. Return only the summary.\n\n"
        f"{text}"
    )
    messages = [{"role": "user", "content": prompt}]
    resp = call_chat_with_fallback(messages, model=MODEL)
    return extract_message_content(resp)


def answer_question(context: str, question: str) -> str:
    if not question or not question.strip():
        return "Error: No question supplied."
    prompt = (
        "You are an academic assistant. Use the context below to answer the question concisely "
        "and without inventing facts.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    )
    messages = [{"role": "user", "content": prompt}]
    resp = call_chat_with_fallback(messages, model=MODEL)
    return extract_message_content(resp)


def ieee_review(text: str) -> str:
    if not text or not text.strip():
        return "Error: No document provided for IEEE review."
    prompt = (
        "You are an IEEE-format reviewer. Provide actionable suggestions to make the following "
        "project documentation conform to IEEE style and structure. Do not invent results or citations. "
        "Return a bullet list of suggestions.\n\n"
        f"{text}"
    )
    messages = [{"role": "user", "content": prompt}]
    resp = call_chat_with_fallback(messages, model=MODEL)
    return extract_message_content(resp)
