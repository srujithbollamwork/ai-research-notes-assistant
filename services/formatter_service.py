# services/formatter_service.py
import os
from dotenv import load_dotenv
load_dotenv()

from services.groq_utils import call_chat_with_fallback, extract_message_content

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def ieee_auto_format(text: str) -> str:
    if not text.strip():
        return "Error: No input text provided."
    prompt = (
        "Reformat the following project documentation into an IEEE-style draft. "
        "Include sections like Abstract, Introduction, Methodology, Results/Discussion, Conclusion, References. "
        "Do not invent references or results.\n\n"
        f"{text}"
    )
    resp = call_chat_with_fallback([{"role": "user", "content": prompt}], model=MODEL)
    return extract_message_content(resp)


def ieee_sectionify(text: str, custom_sections=None) -> str:
    if not text.strip():
        return "Error: No input text provided."
    if not custom_sections:
        custom_sections = ["Abstract", "Introduction", "Methodology", "Results", "Conclusion"]
    section_str = ", ".join(custom_sections)
    prompt = (
        f"Reformat the following text into sections: {section_str}. "
        f"Assign relevant content under each heading. Do not invent facts.\n\n{text}"
    )
    resp = call_chat_with_fallback([{"role": "user", "content": prompt}], model=MODEL)
    return extract_message_content(resp)
