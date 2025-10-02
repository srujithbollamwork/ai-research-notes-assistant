# services/export_service.py
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "research_notes"

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

EXPORTS_DIR = "exports"
os.makedirs(EXPORTS_DIR, exist_ok=True)


def export_note_bundle(user_id: str, note_id: str) -> Optional[str]:
    """
    Export a bundled PDF report containing:
    - Note content
    - AI Summary
    - Related Q&A
    - IEEE Review
    - Citation issues
    - Plagiarism report (if exists)
    """
    note = db.notes.find_one({"_id": note_id, "user_id": user_id})
    if not note:
        return None

    queries = list(db.queries.find({"note_id": note_id, "user_id": user_id}))

    filename = os.path.join(EXPORTS_DIR, f"note_report_{note_id}.pdf")
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    def write_text(title, text, y_pos):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y_pos, title)
        y_pos -= 14
        c.setFont("Helvetica", 10)
        for line in text.split("\n"):
            if y_pos <= 1 * inch:
                c.showPage()
                y_pos = height - 1 * inch
                c.setFont("Helvetica", 10)
            c.drawString(1 * inch, y_pos, line)
            y_pos -= 12
        return y_pos - 20

    y = height - 1 * inch
    y = write_text("📄 Title", note["title"], y)
    y = write_text("📝 Content", note["content"][:3000] + "...", y)

    if note.get("summary"):
        y = write_text("✨ AI Summary", note["summary"], y)

    # Queries: Q&A, reviews, plagiarism, etc.
    for q in queries:
        if q.get("question"):
            y = write_text(f"❓ Q: {q['question']}", f"Answer: {q['answer']}", y)
        if q.get("review"):
            y = write_text("📄 IEEE Review", q["review"], y)
        if q.get("citations"):
            y = write_text("📖 Citation Issues", "\n".join(q["citations"]), y)
        if q.get("type") == "similarity_plagiarism":
            y = write_text("🛡️ Plagiarism Report", str(q["summary"]), y)

    c.save()
    return filename
