import json
import os

from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    def __init__(self, config: ParserConfig):
        self.rates_path = config.RATES_FILE_PATH
        self.history_path = config.HISTORY_FILE_PATH

    def _atomic_write(self, filepath, data):
        """Атомарная запись через временный файл"""
        folder = os.path.dirname(filepath)
        if folder:
            os.makedirs(folder, exist_ok=True)

        temp_file = filepath + ".tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, filepath)

    def save_history(self, new_records: list):
        """Добавляет записи в exchange_rates.json (Append-only)"""
        if not os.path.exists(self.history_path):
            history = []
        else:
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = []

        # Формируем ID для истории (чтобы не дублировать)
        for record in new_records:
            rec_id = f"{record['pair']}_{record['timestamp']}"

            # Подготовка записи для истории
            history_item = {
                "id": rec_id,
                "from_currency": record['from_currency'],
                "to_currency": record['to_currency'],
                "rate": record['rate'],
                "timestamp": record['timestamp'],
                "source": record['source'],
                "meta": record.get("meta", {})
            }
            history.append(history_item)

        self._atomic_write(self.history_path, history)

    def save_snapshot(self, records: list):
        """Обновляет rates.json (Кэш для Core Service)"""
        current_data = {"pairs": {}, "last_refresh": ""}
        if os.path.exists(self.rates_path):
            try:
                with open(self.rates_path, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
            except json.JSONDecodeError:
                pass

        # Обновляем пар
        for rec in records:
            pair = rec['pair']
            current_data["pairs"][pair] = {
                "rate": rec['rate'],
                "updated_at": rec['timestamp'],
                "source": rec['source']
            }

        # Обновляем общее время, если были записи
        if records:
            current_data["last_refresh"] = records[0]['timestamp']

        self._atomic_write(self.rates_path, current_data)
