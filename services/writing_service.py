# services/writing_service.py
import os
from dotenv import load_dotenv
load_dotenv()

from services.groq_utils import call_chat_with_fallback, extract_message_content

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_IEEE = (
    "You are an expert academic writer and a strict reviewer familiar with IEEE paper "
    "structure and style. Produce structured, concise, and formal academic text suitable "
    "for an IEEE conference/journal. Avoid contractions and invented facts."
)


def _build_section_prompt(section: str, text: str, requirements: str | None = None) -> str:
    req = f"\n\nConstraints: {requirements}" if requirements else ""
    return (
        f"Generate an IEEE-style {section} based on the following document or notes.\n\n"
        f"Source material:\n{text}\n\n"
        f"Instructions:\n"
        f"- Produce a clear {section} suitable for an IEEE paper.\n"
        f"- Use formal academic English and concise sentences.\n"
        f"- Do not invent experimental results or citations.\n"
        f"{req}\n\nReturn only the {section} content (no headings)."
    )


def generate_abstract(text: str, max_words: int = 200, requirements: str | None = None) -> str:
    if not text.strip():
        return "Error: No source text provided for abstract generation."
    req = (requirements + f" Limit to approximately {max_words} words.") if requirements else f"Limit to approximately {max_words} words."
    prompt = _build_section_prompt("Abstract", text, req)
    resp = call_chat_with_fallback(
        [{"role": "system", "content": SYSTEM_IEEE}, {"role": "user", "content": prompt}],
        model=MODEL
    )
    return extract_message_content(resp)


def generate_introduction(text: str, max_paragraphs: int = 3, requirements: str | None = None) -> str:
    if not text.strip():
        return "Error: No source text provided for introduction generation."
    req = (requirements + f" Use up to {max_paragraphs} paragraphs.") if requirements else f"Use up to {max_paragraphs} paragraphs."
    prompt = _build_section_prompt("Introduction", text, req)
    resp = call_chat_with_fallback(
        [{"role": "system", "content": SYSTEM_IEEE}, {"role": "user", "content": prompt}],
        model=MODEL
    )
    return extract_message_content(resp)


def generate_conclusion(text: str, max_sentences: int = 6, requirements: str | None = None) -> str:
    if not text.strip():
        return "Error: No source text provided for conclusion generation."
    req = (requirements + f" Keep it within {max_sentences} sentences.") if requirements else f"Keep it within {max_sentences} sentences."
    prompt = _build_section_prompt("Conclusion", text, req)
    resp = call_chat_with_fallback(
        [{"role": "system", "content": SYSTEM_IEEE}, {"role": "user", "content": prompt}],
        model=MODEL
    )
    return extract_message_content(resp)


def generate_custom_section(title: str, text: str, constraints: str | None = None) -> str:
    if not text.strip():
        return f"Error: No source text provided for {title} generation."
    prompt = _build_section_prompt(title, text, constraints)
    resp = call_chat_with_fallback(
        [{"role": "system", "content": SYSTEM_IEEE}, {"role": "user", "content": prompt}],
        model=MODEL
    )
    return extract_message_content(resp)
