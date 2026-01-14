import json
import os
import shlex

from prettytable import PrettyTable

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import SystemCore
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater


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
        return self.core.current_user.username if self.core.current_user else "guest"

    def _parse_args(self, args_list):
        """Превращает ['--key', 'value'] в {'key': 'value'}"""
        parsed = {}
        iterator = iter(args_list)
        for item in iterator:
            if item.startswith('--'):
                try:
                    parsed[item[2:]] = next(iterator)
                except StopIteration:
                    pass
        return parsed

    def _handle_command(self, command, args):
        kwargs = self._parse_args(args)

        # Блок обработки исключений доменной логики
        try:
            if command == 'register':
                if 'username' in kwargs and 'password' in kwargs:
                    uid = self.core.register(kwargs['username'], kwargs['password'])
                    print(f"Пользователь зарегистрирован (id={uid})")
                else:
                    print("Usage: register --username X --password Y")

            elif command == 'login':
                if 'username' in kwargs and 'password' in kwargs:
                    name = self.core.login(kwargs['username'], kwargs['password'])
                    print(f"Вы вошли как '{name}'")
                else:
                    print("Usage: login --username X --password Y")

            elif command == 'show-portfolio':
                base = kwargs.get('base', 'USD')
                wallets, total = self.core.get_portfolio_info(base)

                t = PrettyTable(['Currency', 'Info', 'Balance', f'Value ({base})'])
                t.align = "l"
                for w in wallets:
                    t.add_row([w['code'], w['display'],
                               f"{w['balance']:.4f}", f"{w['value']:.2f}"])
                print(t)
                print(f"ИТОГО: {total:.2f} {base}")

            elif command == 'buy':
                if 'currency' in kwargs and 'amount' in kwargs:
                    rate, cost = self.core.buy_currency(
                        kwargs['currency'], float(kwargs['amount']))
                    print(f"Покупка успешна! Курс: {rate}, Списано: {cost:.2f} USD")
                else:
                    print("Usage: buy --currency BTC --amount 0.05")

            elif command == 'sell':
                if 'currency' in kwargs and 'amount' in kwargs:
                    rate, rev = self.core.sell_currency(
                        kwargs['currency'], float(kwargs['amount']))
                    print(f"Продажа успешна! Выручено: {rev:.2f} USD")
                else:
                    print("Usage: sell --currency BTC --amount 0.05")

            elif command == 'get-rate':
                f, t = kwargs.get('from'), kwargs.get('to')
                if f and t:
                    rate, dt = self.core.get_rate(f, t)
                    print(f"Курс {f}->{t}: {rate} (от {dt})")
                else:
                    print("Usage: get-rate --from USD --to BTC")

            elif command == 'help':
                print("Команды: "
                      "register, login, buy, sell, show-portfolio, get-rate, exit")
            elif command == 'update-rates':
                source = kwargs.get('source')
                print("Запуск обновления курсов (это может занять время)...")
                updater = RatesUpdater()
                count = updater.run_update(source_filter=source)
                if count > 0:
                    print(f"Обновление завершено. Обновлено пар: {count}")
                else:
                    print("Не удалось обновить курсы (см. логи). "
                          "Возможно, отсутствует API Key или перебои сети.")

            elif command == 'show-rates':
                config = ParserConfig()
                if not os.path.exists(config.RATES_FILE_PATH):
                    print("Кэш курсов пуст. Выполните 'update-rates'.")
                    return

                with open(config.RATES_FILE_PATH, 'r') as f:
                    data = json.load(f)

                pairs = data.get("pairs", {})
                last_refresh = data.get("last_refresh", "N/A")

                # Фильтры
                target_curr = kwargs.get('currency')
                is_top = kwargs.get('top')

                result_list = []
                for pair, info in pairs.items():
                    if target_curr and target_curr.upper() not in pair:
                        continue
                    result_list.append((pair, info['rate'], info['updated_at']))

                # Сортировка
                if is_top:
                    # Сортируем по цене (rate) убыванию
                    result_list.sort(key=lambda x: x[1], reverse=True)
                    limit = int(is_top)
                    result_list = result_list[:limit]
                else:
                    # По алфавиту
                    result_list.sort(key=lambda x: x[0])

                if not result_list:
                    print(f"Курсы не найдены (фильтр: {target_curr or 'None'}).")
                else:
                    t = PrettyTable(['Pair', 'Rate (USD)', 'Updated At'])
                    t.align = "l"
                    for r in result_list:
                        t.add_row([r[0], f"{r[1]:.5f}", r[2]])
                    print(f"Актуальные курсы (обновлено: {last_refresh}):")
                    print(t)
            else:
                print(f"Неизвестная команда: {command}")

        # Обработка ожидаемых бизнес-ошибок
        except InsufficientFundsError as e:
            print(f"Ошибка операции: {e}")
        except CurrencyNotFoundError as e:
            print(f"Ошибка валюты: {e}. "
                  f"Используйте общепринятые коды (USD, BTC, ETH).")
        except ApiRequestError as e:
            print(f"Ошибка сети: {e}")
        except ValueError as e:
            print(f"Ошибка данных: {e}")
        except PermissionError as e:
            print(f"Доступ запрещен: {e}")