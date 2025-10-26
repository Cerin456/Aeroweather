# utils/auth.py
import json
from pathlib import Path
from passlib.hash import pbkdf2_sha256 as bcrypt

USERS_FILE = Path("data/users.json")
USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_users():
    if not USERS_FILE.exists():
        return {}
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))

def save_users(users: dict):
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")

def verify_user(username: str, password: str) -> bool:
    users = load_users()
    user = users.get(username)
    if not user:
        return False
    return bcrypt.verify(password, user["password_hash"])

def create_user(username: str, password: str):
    users = load_users()
    if username in users:
        raise ValueError("User already exists")
    users[username] = {"password_hash": bcrypt.hash(password)}
    save_users(users)
    return True

# helper to create demo user (call from app if needed)
def ensure_demo_user():
    users = load_users()
    if "demo" not in users:
        create_user("demo", "demo123")
