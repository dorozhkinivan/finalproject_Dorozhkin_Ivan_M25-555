import os
from dataclasses import dataclass


@dataclass
class ParserConfig:
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY")

    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    BASE_CURRENCY: str = "USD"
    REQUEST_TIMEOUT: int = 15

    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB", "JPY", "CNY")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL", "USDT")

    CRYPTO_ID_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "USDT": "tether"
    }

    RATES_FILE_PATH: str = os.path.join("data", "rates.json")
    HISTORY_FILE_PATH: str = os.path.join("data", "exchange_rates.json")
