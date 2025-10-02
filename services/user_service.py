import bcrypt
from database.db import db
from datetime import datetime

def register_user(name, email, password):
    users = db.users
    if users.find_one({"email": email}):
        return False, "User already exists"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    user = {"name": name, "email": email, "password": hashed, "created_at": datetime.utcnow()}
    users.insert_one(user)
    return True, "Registration successful"

def login_user(email, password):
    user = db.users.find_one({"email": email})
    if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return True, user
    return False, "Invalid email or password"
