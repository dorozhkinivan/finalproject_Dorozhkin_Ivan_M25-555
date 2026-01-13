import shlex

from prettytable import PrettyTable

from valutatrade_hub.core.usecases import SystemCore


class CLI:
    def __init__(self):
        self.core = SystemCore()

    def run(self):
        print("Добро пожаловать в ValutaTrade Hub! Введите help для списка команд.")
        while True:
            try:
                user_input = input(f"{self._get_prompt()}> ").strip()
                if not user_input:
                    continue

                # shlex позволяет безопасно парсить строки с кавычками
                parts = shlex.split(user_input)
                command = parts[0].lower()
                args = parts[1:]

                if command in ('exit', 'quit'):
                    print("До свидания!")
                    break

                self._handle_command(command, args)

            except KeyboardInterrupt:
                print("\nВыход...")
                break
            except Exception as e:
                print(f"Ошибка: {e}")

    def _get_prompt(self):
        if self.core.current_user:
            return self.core.current_user.username
        return "guest"

    def _parse_args(self, args_list):
        """Превращает ['--key', 'value'] в {'key': 'value'}"""
        parsed = {}
        iterator = iter(args_list)
        for item in iterator:
            if item.startswith('--'):
                key = item[2:]
                try:
                    value = next(iterator)
                    parsed[key] = value
                except StopIteration:
                    print(f"Предупреждение: аргумент {key} без значения")
        return parsed

    def _handle_command(self, command, args):
        kwargs = self._parse_args(args)

        if command == 'register':
            u = kwargs.get('username')
            p = kwargs.get('password')
            if u and p:
                uid = self.core.register(u, p)
                print(f"Пользователь '{u}' зарегистрирован (id={uid}). "
                      f"Войдите через login.")
            else:
                print("Использование: register --username <name> --password <pass>")

        elif command == 'login':
            u = kwargs.get('username')
            p = kwargs.get('password')
            if u and p:
                name = self.core.login(u, p)
                print(f"Вы вошли как '{name}'")
            else:
                print("Использование: login --username <name> --password <pass>")

        elif command == 'show-portfolio':
            base = kwargs.get('base', 'USD')
            try:
                wallets, total = self.core.get_portfolio_info(base)
                t = PrettyTable(['Currency', 'Balance', f'Value ({base})'])
                for w in wallets:
                    t.add_row([w[0], f"{w[1]:.4f}", f"{w[2]:.2f}"])
                print(f"Портфель пользователя '{self.core.current_user.username}':")
                print(t)
                print(f"ИТОГО: {total:.2f} {base}")
            except PermissionError as e:
                print(e)

        elif command == 'buy':
            curr = kwargs.get('currency')
            amt = kwargs.get('amount')
            if curr and amt:
                try:
                    rate, cost = self.core.buy_currency(curr, float(amt))
                    print(f"Покупка выполнена: {amt} {curr} по курсу {rate}")
                    print(f"Потрачено (оценочно): {cost:.2f} USD")
                except ValueError as e:
                    print(f"Ошибка данных: {e}")
                except PermissionError as e:
                    print(e)
            else:
                print("Использование: buy --currency <BTC> --amount <0.05>")

        elif command == 'sell':
            curr = kwargs.get('currency')
            amt = kwargs.get('amount')
            if curr and amt:
                try:
                    rate, revenue = self.core.sell_currency(curr, float(amt))
                    print(f"Продажа выполнена: {amt} {curr}")
                    print(f"Выручено (оценочно): {revenue:.2f} USD")
                except ValueError as e:
                    print(f"Ошибка: {e}")
                except PermissionError as e:
                    print(e)
            else:
                print("Использование: sell --currency <BTC> --amount <0.05>")

        elif command == 'get-rate':
            fr = kwargs.get('from')
            to = kwargs.get('to')
            if fr and to:
                rate, dt = self.core.get_rate(fr, to)
                if rate:
                    print(f"Курс {fr}->{to}: {rate} (обновлено: {dt})")
                else:
                    print(f"Курс {fr}->{to} не найден "
                          f"(ParserService не работает или нет данных)")
            else:
                print("Использование: get-rate --from USD --to BTC")

        elif command == 'help':
            print("Доступные команды: register, login, "
                  "show-portfolio, buy, sell, get-rate, exit")

        else:
            print(f"Неизвестная команда: {command}")