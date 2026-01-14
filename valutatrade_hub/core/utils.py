import hashlib
import uuid


def generate_salt() -> str:
    return uuid.uuid4().hex[:8]  # Простая случайная строка


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode()).hexdigest()