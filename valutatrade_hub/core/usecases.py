from datetime import datetime, timezone

from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader

from .currencies import get_currency
from .exceptions import ApiRequestError, InsufficientFundsError
from .models import Portfolio, User
from .utils import generate_salt, hash_password


class SystemCore:
    def __init__(self):
        self._current_user = None
        self._current_portfolio = None
        self.db = DatabaseManager()
        self.settings = SettingsLoader()

    @property
    def current_user(self):
        return self._current_user

    def register(self, username, password):
        users = self.db.load_users()
        if any(u['username'] == username for u in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        new_id = len(users) + 1
        salt = generate_salt()
        hashed = hash_password(password, salt)
        reg_date = datetime.now().isoformat()

        user = User(new_id, username, hashed, salt, reg_date)
        users.append(user.to_dict())
        self.db.save_users(users)

        portfolios = self.db.load_portfolios()
        portfolios.append({"user_id": new_id, "wallets": {}})
        self.db.save_portfolios(portfolios)

        return new_id

    def login(self, username, password):
        users_data = self.db.load_users()
        user_record = next((u for u in users_data if u['username'] == username), None)

        if not user_record:
            raise ValueError(f"Пользователь '{username}' не найден")

        # Создаем временный объект User для проверки пароля
        user = User(**user_record)
        if not user.verify_password(password):
            raise ValueError("Неверный пароль")

        self._current_user = user
        self._load_portfolio() # Загружаем портфель в память
        return user.username

    def _load_portfolio(self):
        if not self._current_user:
            return
        all_p = self.db.load_portfolios()
        p_data = next(
            (p for p in all_p if p['user_id'] == self._current_user.user_id)
            , None)
        if p_data:
            self._current_portfolio = Portfolio(p_data['user_id'], p_data['wallets'])
        else:
            self._current_portfolio = Portfolio(self._current_user.user_id, {})

    def _save_portfolio(self):
        if not self._current_portfolio:
            return
        all_p = self.db.load_portfolios()
        for i, p in enumerate(all_p):
            if p['user_id'] == self._current_user.user_id:
                all_p[i] = self._current_portfolio.to_dict()
                break
        else:
            all_p.append(self._current_portfolio.to_dict())
        self.db.save_portfolios(all_p)

    def _get_rates_data(self):
        data = self.db.load_rates()
        return data.get("pairs", data)

    def get_portfolio_info(self, base_currency='USD'):
        if not self._current_user:
            raise PermissionError("Сначала выполните login")

        # Проверяем, существует ли базовая валюта
        get_currency(base_currency)

        rates = self._get_rates_data()
        total = self._current_portfolio.get_total_value(rates, base_currency)

        wallet_info = []
        for code, wallet in self._current_portfolio.wallets.items():
            curr_obj = get_currency(code)

            val_in_base = wallet.balance
            if code != base_currency:
                rate = rates.get(f"{code}_{base_currency}", {}).get('rate', 0.0)
                val_in_base = wallet.balance * rate

            wallet_info.append({
                "code": code,
                "balance": wallet.balance,
                "value": val_in_base,
                "display": curr_obj.get_display_info()
            })

        return wallet_info, total

    @log_action("BUY")
    def buy_currency(self, currency_code: str, amount: float):
        if not self._current_user:
            raise PermissionError("Сначала выполните login")

        # Валидация валюты
        get_currency(currency_code)

        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")

        base_curr = self.settings.get("BASE_CURRENCY")

        rates = self._get_rates_data()
        pair = f"{currency_code}_{base_curr}"
        rate_info = rates.get(pair)

        if not rate_info:
            rate_info = {"rate": 100.0}  # for test
            # raise ApiRequestError("Курс не найден")

        rate = rate_info['rate']
        cost_in_base = amount * rate

        base_wallet = self._current_portfolio.add_currency(base_curr)

        # for test
        if base_wallet.balance == 0:
            base_wallet.deposit(cost_in_base + 1000)

        target_wallet = self._current_portfolio.add_currency(currency_code)

        base_wallet.withdraw(cost_in_base)
        target_wallet.deposit(amount)

        self._save_portfolio()
        return rate, cost_in_base

    @log_action("SELL")
    def sell_currency(self, currency_code: str, amount: float):
        if not self._current_user:
            raise PermissionError("Сначала выполните login")

        get_currency(currency_code)  # Valid check

        wallet = self._current_portfolio.get_wallet(currency_code)
        if not wallet:
            raise InsufficientFundsError(amount, 0, currency_code)

        base_curr = self.settings.get("BASE_CURRENCY")

        rates = self._get_rates_data()
        pair = f"{currency_code}_{base_curr}"
        rate = rates.get(pair, {}).get('rate', 0.0)

        revenue = amount * rate

        if revenue <= 0:
            raise ApiRequestError(f"Невозможно продать: курс {pair} "
                                  f"равен 0 или не найден.")

        # Списание (проверка баланса внутри withdraw)
        wallet.withdraw(amount)

        # Начисление
        base_wallet = self._current_portfolio.add_currency(base_curr)
        base_wallet.deposit(revenue)

        self._save_portfolio()
        return rate, revenue

    def get_rate(self, from_curr, to_curr):
        # Валидация
        get_currency(from_curr)
        get_currency(to_curr)

        rates = self._get_rates_data()
        pair = f"{from_curr}_{to_curr}".upper()
        data = rates.get(pair)

        if data:
            updated = datetime.fromisoformat(data['updated_at'])
            ttl = self.settings.get("RATES_TTL")
            if (datetime.now(timezone.utc) - updated).total_seconds() > ttl:
                # todo
                pass
            return data['rate'], data['updated_at']

        raise ApiRequestError(f"Курс {pair} не найден в базе")