import os
from typing import Any


class SettingsLoader:
    _instance = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsLoader, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        # Базовые пути
        base_dir = os.getcwd()
        data_dir = os.path.join(base_dir, "data")
        logs_dir = os.path.join(base_dir, "logs")

        # Создаем папки, если их нет
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)

        self._config = {
            "DATA_DIR": data_dir,
            "LOGS_DIR": logs_dir,
            "USERS_FILE": os.path.join(data_dir, "users.json"),
            "PORTFOLIOS_FILE": os.path.join(data_dir, "portfolios.json"),
            "RATES_FILE": os.path.join(data_dir, "rates.json"),
            "LOG_FILE": os.path.join(logs_dir, "actions.log"),
            "RATES_TTL": 300,  # 5 минут свежести данных
            "BASE_CURRENCY": "USD",
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "%(asctime)s %(levelname)s %(message)s"
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def reload(self):
        """Перезагрузка конфигурации"""
        self._load()