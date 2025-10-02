from datetime import datetime

def create_note(title, content, summary=None):
    return {
        "title": title,
        "content": content,
        "summary": summary,
        "created_at": datetime.utcnow()
    }
