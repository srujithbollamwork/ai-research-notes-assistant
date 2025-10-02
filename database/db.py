import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "research_notes"

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

def insert_note(note):
    result = db.notes.insert_one(note)
    return str(result.inserted_id)

def get_all_notes():
    return list(db.notes.find())

def get_note_by_id(note_id):
    return db.notes.find_one({"_id": note_id})

def test_connection():
    try:
        db.command("ping")
        return "✅ MongoDB connection successful"
    except Exception as e:
        return f"❌ MongoDB connection failed: {e}"
