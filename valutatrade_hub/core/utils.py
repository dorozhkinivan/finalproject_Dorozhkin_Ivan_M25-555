import hashlib
import json
import os
import uuid

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Инициализация пустых файлов, если их нет
    for f in [USERS_FILE, PORTFOLIOS_FILE]:
        if not os.path.exists(f):
            with open(f, 'w') as file:
                json.dump([], file)

    if not os.path.exists(RATES_FILE):
        with open(RATES_FILE, 'w') as file:
            json.dump({}, file)


def load_json(filepath: str):
    ensure_data_dir()
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return [] if filepath != RATES_FILE else {}


def save_json(filepath: str, data):
    ensure_data_dir()
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)


def generate_salt() -> str:
    return uuid.uuid4().hex[:8]  # Простая случайная строка


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode()).hexdigest()