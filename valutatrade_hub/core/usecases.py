from datetime import datetime

from .models import Portfolio, User
from .utils import (
    PORTFOLIOS_FILE,
    RATES_FILE,
    USERS_FILE,
    generate_salt,
    hash_password,
    load_json,
    save_json,
)


class SystemCore:
    def __init__(self):
        self._current_user = None
        self._current_portfolio = None

    @property
    def current_user(self):
        return self._current_user

    def register(self, username, password):
        users_data = load_json(USERS_FILE)

        # 1. Проверка уникальности
        for u in users_data:
            if u['username'] == username:
                raise ValueError(f"Имя пользователя '{username}' уже занято")

        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        # 2. Создание ID и хеширование
        new_id = len(users_data) + 1
        salt = generate_salt()
        hashed = hash_password(password, salt)
        reg_date = datetime.now().isoformat()

        user = User(new_id, username, hashed, salt, reg_date)

        # 3. Сохранение пользователя
        users_data.append(user.to_dict())
        save_json(USERS_FILE, users_data)

        # 4. Создание пустого портфеля
        portfolios_data = load_json(PORTFOLIOS_FILE)
        # Формат portfolios.json - список объектов
        new_portfolio_record = {
            "user_id": new_id,
            "wallets": {}
        }
        portfolios_data.append(new_portfolio_record)
        save_json(PORTFOLIOS_FILE, portfolios_data)

        return new_id

    def login(self, username, password):
        users_data = load_json(USERS_FILE)
        user_record = next((u for u in users_data if u['username'] == username), None)

        if not user_record:
            raise ValueError(f"Пользователь '{username}' не найден")

        # Создаем временный объект User для проверки пароля
        user = User(**user_record)
        if not user.verify_password(password):
            raise ValueError("Неверный пароль")

        self._current_user = user
        self._load_portfolio()  # Загружаем портфель в память
        return user.username

    def _load_portfolio(self):
        if not self._current_user:
            return
        all_portfolios = load_json(PORTFOLIOS_FILE)
        p_data = next((p for p in all_portfolios if p['user_id'] ==
                       self._current_user.user_id), None)

        if p_data:
            self._current_portfolio = Portfolio(p_data['user_id'], p_data['wallets'])
        else:
            # Если вдруг портфеля нет (например, стерли файл), создаем пустой
            self._current_portfolio = Portfolio(self._current_user.user_id, {})

    def _save_portfolio(self):
        if not self._current_portfolio:
            return
        all_portfolios = load_json(PORTFOLIOS_FILE)

        # Ищем индекс портфеля текущего юзера и обновляем
        for i, p in enumerate(all_portfolios):
            if p['user_id'] == self._current_user.user_id:
                all_portfolios[i] = self._current_portfolio.to_dict()
                break
        else:
            # Если не нашли, добавляем
            all_portfolios.append(self._current_portfolio.to_dict())

        save_json(PORTFOLIOS_FILE, all_portfolios)

    def get_portfolio_info(self, base_currency='USD'):
        if not self._current_user:
            raise PermissionError("Сначала выполните login")

        rates = load_json(RATES_FILE)
        total = self._current_portfolio.get_total_value(rates, base_currency)

        wallet_info = []
        for code, wallet in self._current_portfolio.wallets.items():
            # Оценка конкретного кошелька в базе
            val_in_base = wallet.balance
            if code != base_currency:
                rate = rates.get(f"{code}_{base_currency}", {}).get('rate', 0.0)
                val_in_base = wallet.balance * rate

            wallet_info.append((code, wallet.balance, val_in_base))

        return wallet_info, total

    def buy_currency(self, currency_code: str, amount: float):
        if not self._current_user:
            raise PermissionError("Сначала выполните login")

        currency_code = currency_code.upper()
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")


        # Получаем курс
        rates = load_json(RATES_FILE)
        pair = f"{currency_code}_USD"
        rate_info = rates.get(pair)

        # чтобы код работал
        current_rate = rate_info['rate'] if rate_info else 100.0

        cost_in_usd = amount * current_rate

        wallet_usd = self._current_portfolio.get_wallet('USD')
        # Если кошелька USD нет, или денег нет
        if not wallet_usd or wallet_usd.balance < cost_in_usd:
            pass

        usd_wallet = self._current_portfolio.add_currency('USD')

        if usd_wallet.balance == 0:
            usd_wallet.deposit(10000.0)  # Стартовый капитал

        target_wallet = self._current_portfolio.add_currency(currency_code)

        usd_wallet.withdraw(cost_in_usd)
        target_wallet.deposit(amount)

        self._save_portfolio()
        return current_rate, cost_in_usd

    def sell_currency(self, currency_code: str, amount: float):
        if not self._current_user:
            raise PermissionError("Сначала выполните login")

        currency_code = currency_code.upper()
        wallet = self._current_portfolio.get_wallet(currency_code)

        if not wallet:
            raise ValueError(f"У вас нет кошелька {currency_code}")

        wallet.withdraw(amount)  # Проверки внутри

        # Начисляем USD
        rates = load_json(RATES_FILE)
        pair = f"{currency_code}_USD"
        rate = rates.get(pair, {}).get('rate', 0.0)
        revenue = amount * rate

        usd_wallet = self._current_portfolio.add_currency('USD')
        usd_wallet.deposit(revenue)

        self._save_portfolio()
        return rate, revenue

    def get_rate(self, from_curr, to_curr):
        rates = load_json(RATES_FILE)
        pair = f"{from_curr}_{to_curr}".upper()
        data = rates.get(pair)
        if data:
            return data['rate'], data['updated_at']
        return None, None