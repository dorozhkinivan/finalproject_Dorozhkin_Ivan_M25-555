import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests

from valutatrade_hub.core.exceptions import ApiRequestError

from .config import ParserConfig


class BaseApiClient(ABC):
    def __init__(self, config: ParserConfig):
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> List[Dict[str, Any]]:
        """
        Возвращает список словарей формата:
        {
            "pair": "BTC_USD",
            "rate": 50000.0,
            "timestamp": "ISO_STR",
            "source": "SourceName",
            "meta": {...}
        }
        """
        pass


class CoinGeckoClient(BaseApiClient):
    def fetch_rates(self) -> List[Dict[str, Any]]:
        # Формируем список ID: bitcoin,ethereum...
        ids = list(self.config.CRYPTO_ID_MAP.values())
        ids_str = ",".join(ids)
        params = {
            "ids": ids_str,
            "vs_currencies": self.config.BASE_CURRENCY.lower()
        }

        # bitcoin -> BTC (чтобы восстановить тикер)
        id_to_ticker = {v: k for k, v in self.config.CRYPTO_ID_MAP.items()}

        start_time = time.time()
        try:
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ApiRequestError(f"CoinGecko Error: {e}")

        duration = int((time.time() - start_time) * 1000)
        results = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for coin_id, rates in data.items():
            ticker = id_to_ticker.get(coin_id)
            if not ticker:
                continue

            price = rates.get(self.config.BASE_CURRENCY.lower())
            if price:
                results.append({
                    "pair": f"{ticker}_{self.config.BASE_CURRENCY}",
                    "from_currency": ticker,
                    "to_currency": self.config.BASE_CURRENCY,
                    "rate": float(price),
                    "timestamp": now_iso,
                    "source": "CoinGecko",
                    "meta": {
                        "raw_id": coin_id,
                        "request_ms": duration,
                        "status_code": response.status_code
                    }
                })
        return results


class ExchangeRateApiClient(BaseApiClient):
    def fetch_rates(self) -> List[Dict[str, Any]]:
        api_key = self.config.EXCHANGERATE_API_KEY
        if not api_key:
            raise ApiRequestError("ExchangeRate API Key not found in env vars")

        base = self.config.BASE_CURRENCY
        url = f"{self.config.EXCHANGERATE_API_URL}/{api_key}/latest/{base}"

        start_time = time.time()
        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API Error: {e}")

        if data.get("result") != "success":
            raise ApiRequestError(f"API Error: {data.get('error-type')}")

        duration = int((time.time() - start_time) * 1000)
        results = []
        now_iso = datetime.now(timezone.utc).isoformat()

        api_rates = data.get("conversion_rates", {})

        for code in self.config.FIAT_CURRENCIES:
            # API возвращает: Сколько Валюты дают за 1 USD. (e.g. RUB=98)
            # Нам нужно: Цену валюты в USD. (1 RUB = 0.0102 USD)
            rate_in_base = api_rates.get(code)

            if rate_in_base:
                # Инвертируем курс
                usd_price = 1 / rate_in_base

                results.append({
                    "pair": f"{code}_{base}",
                    "from_currency": code,
                    "to_currency": base,
                    "rate": usd_price,
                    "timestamp": now_iso,
                    "source": "ExchangeRate-API",
                    "meta": {
                        "request_ms": duration,
                        "status_code": response.status_code
                    }
                })
        return results
