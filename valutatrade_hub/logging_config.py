import logging
import logging.handlers

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging():
    settings = SettingsLoader()
    log_file = settings.get("LOG_FILE")
    log_format = settings.get("LOG_FORMAT")

    # Ротация: макс 1 МБ, храним 3 файла бэкапа
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter(log_format))

    logger = logging.getLogger("ValutaTrade")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger

logger = setup_logging()