import json
import os

from .settings import SettingsLoader


class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._settings = SettingsLoader()
        return cls._instance

    def _read_json(self, filepath: str, default=None):
        if not os.path.exists(filepath):
            return default if default is not None else []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default if default is not None else []

    def _write_json(self, filepath: str, data):
        # Атомарная запись
        temp_file = filepath + ".tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp_file, filepath)

    # Методы для конкретных сущностей
    def load_users(self):
        return self._read_json(self._settings.get("USERS_FILE"), [])

    def save_users(self, data):
        self._write_json(self._settings.get("USERS_FILE"), data)

    def load_portfolios(self):
        return self._read_json(self._settings.get("PORTFOLIOS_FILE"), [])

    def save_portfolios(self, data):
        self._write_json(self._settings.get("PORTFOLIOS_FILE"), data)

    def load_rates(self):
        return self._read_json(self._settings.get("RATES_FILE"), {})

    def save_rates(self, data):
        self._write_json(self._settings.get("RATES_FILE"), data)