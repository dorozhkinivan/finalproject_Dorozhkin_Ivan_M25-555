import hashlib
from datetime import datetime
from typing import Dict


class User:
    def __init__(self, user_id: int, username: str,
                 hashed_password: str, salt: str, registration_date: str):
        self._user_id = user_id
        if not username:
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = datetime.fromisoformat(registration_date)

    @property
    def username(self) -> str:
        return self._username

    @property
    def user_id(self) -> int:
        return self._user_id

    def get_user_info(self) -> str:
        return (f"ID: {self._user_id}, User: {self._username}, "
                f"Reg: {self._registration_date}")

    def verify_password(self, password: str) -> bool:
        # Простейшая проверка хеша: hash(pass + salt)
        check_hash = hashlib.sha256((password + self._salt).encode()).hexdigest()
        return check_hash == self._hashed_password

    def change_password(self, new_password: str):
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        new_hash = hashlib.sha256((new_password + self._salt).encode()).hexdigest()
        self._hashed_password = new_hash

    def to_dict(self) -> dict:
        """Для сохранения в JSON"""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self._balance = 0.0  # Инициализируем нулем, потом используем сеттер
        self.balance = float(balance)  # Используем сеттер для валидации

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = value

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance += amount

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self.balance:
            raise ValueError(f"Недостаточно средств. Доступно: {self.balance}")
        self.balance -= amount

    def get_balance_info(self) -> str:
        return f"{self.currency_code}: {self.balance:.4f}"

    def to_dict(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self.balance
        }


class Portfolio:
    def __init__(self, user_id: int, wallets_data: Dict[str, dict] = None):
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = {}

        if wallets_data:
            for code, data in wallets_data.items():
                self._wallets[code] = Wallet(data['currency_code'], data['balance'])

    @property
    def user(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return self._wallets.copy()

    def get_wallet(self, currency_code: str) -> Wallet:
        return self._wallets.get(currency_code.upper())

    def add_currency(self, currency_code: str) -> Wallet:
        code = currency_code.upper()
        if code not in self._wallets:
            new_wallet = Wallet(code, 0.0)
            self._wallets[code] = new_wallet
        return self._wallets[code]

    def get_total_value(self, rates: dict, base_currency='USD') -> float:
        total = 0.0
        for wallet in self._wallets.values():
            if wallet.currency_code == base_currency:
                total += wallet.balance
                continue

            # Ищем пару CURRENCY_BASE
            pair = f"{wallet.currency_code}_{base_currency}"
            rate_info = rates.get(pair)

            if rate_info:
                rate = rate_info.get('rate', 0.0)
                total += wallet.balance * rate
            else:
                # Попробуем обратный курс простейшим образом (для примера)
                pass
                # Если курса нет, считаем как 0 (или можно кидать ошибку)
        return total

    def to_dict(self) -> dict:
        return {
            "user_id": self._user_id,
            "wallets": {code: w.to_dict() for code, w in self._wallets.items()}
        }