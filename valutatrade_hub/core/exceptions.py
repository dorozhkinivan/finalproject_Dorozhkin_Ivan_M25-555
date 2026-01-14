class InsufficientFundsError(Exception):
    def __init__(self, required, available, currency_code):
        self.message = (f"Недостаточно средств: "
                        f"доступно {available} {currency_code}, "
                        f"требуется {required} {currency_code}")
        super().__init__(self.message)

class CurrencyNotFoundError(Exception):
    def __init__(self, code):
        self.message = f"Неизвестная валюта '{code}'"
        super().__init__(self.message)

class ApiRequestError(Exception):
    def __init__(self, reason):
        self.message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(self.message)