# services/tag_service.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "research_notes"

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]


def add_tags_to_note(note_id, tags: List[str]):
    """Attach tags to a note"""
    db.notes.update_one({"_id": note_id}, {"$set": {"tags": tags}})


def get_notes_by_tag(user_id: str, tag: str):
    """Fetch notes that contain a specific tag"""
    return list(db.notes.find({"user_id": user_id, "tags": {"$in": [tag]}}))
