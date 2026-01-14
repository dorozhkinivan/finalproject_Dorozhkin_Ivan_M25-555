import functools

from valutatrade_hub.logging_config import logger


def log_action(action_name):
    """
    Декоратор для логирования действий (BUY, SELL, etc.)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _self = args[0]
            username = _self.current_user.username if _self.current_user else "GUEST"

            # Собираем параметры для лога
            currency = kwargs.get('currency_code', 'N/A')
            amount = kwargs.get('amount', 0)

            try:
                result = func(*args, **kwargs)

                rate_info = ""
                if isinstance(result, tuple) and len(result) >= 1:
                    rate_info = f"rate={result[0]} val={result[1]:.2f}"

                msg = (f"{action_name} user='{username}' currency='{currency}' "
                       f"amount={amount} {rate_info} result=OK")
                logger.info(msg)

                return result

            except Exception as e:
                # Логируем ошибку и пробрасываем дальше
                error_type = type(e).__name__
                msg = (f"{action_name} user='{username}' currency='{currency}' "
                       f"amount={amount} result=ERROR error={error_type} msg='{e}'")
                logger.error(msg)
                raise e

        return wrapper

    return decorator