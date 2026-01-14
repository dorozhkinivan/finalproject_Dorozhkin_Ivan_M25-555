from abc import ABC, abstractmethod
from typing import Dict

from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, code: str, name: str):
        self.code = code.upper()
        self.name = name

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает форматированную строку описания"""
        pass

class FiatCurrency(Currency):
    def __init__(self, code: str, name: str, issuing_country: str):
        super().__init__(code, name)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    def __init__(self, code: str, name: str, algorithm: str, market_cap: str = "N/A"):
        super().__init__(code, name)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return (f"[CRYPTO] {self.code} — {self.name} "
                f"(Algo: {self.algorithm}, MCAP: {self.market_cap})")

# Реестр поддерживаемых валют
_SUPPORTED_CURRENCIES: Dict[str, Currency] = {
    # FIAT
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russia"),
    # CRYPTO
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", "1.2T"),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", "400B"),
    "USDT": CryptoCurrency("USDT", "Tether", "ERC-20", "100B"),
}

def get_currency(code: str) -> Currency:
    code_upper = code.upper()
    if code_upper not in _SUPPORTED_CURRENCIES:
        raise CurrencyNotFoundError(code)
    return _SUPPORTED_CURRENCIES[code_upper]