import logging

from valutatrade_hub.core.exceptions import ApiRequestError

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig
from .storage import RatesStorage

logger = logging.getLogger("ValutaTrade")


class RatesUpdater:
    def __init__(self):
        self.config = ParserConfig()
        self.storage = RatesStorage(self.config)
        self.clients = [
            CoinGeckoClient(self.config),
            ExchangeRateApiClient(self.config)
        ]

    def run_update(self, source_filter=None):
        logger.info("Starting rates update...")
        all_rates = []

        for client in self.clients:
            client_name = client.__class__.__name__

            # Фильтр по источнику (если указан аргумент --source)
            if source_filter:
                if ("coingecko" in source_filter.lower() and
                        "CoinGecko" not in client_name):
                    continue
                if ("exchange" in source_filter.lower() and
                        "Exchange" not in client_name):
                    continue

            try:
                logger.info(f"Fetching from {client_name}...")
                rates = client.fetch_rates()
                all_rates.extend(rates)
                logger.info(f"Success {client_name}: obtained {len(rates)} rates.")
            except ApiRequestError as e:
                logger.error(f"Failed to fetch from {client_name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in {client_name}: {e}")

        if all_rates:
            logger.info(f"Writing {len(all_rates)} rates to storage...")
            self.storage.save_history(all_rates)
            self.storage.save_snapshot(all_rates)
            logger.info("Update completed.")
            return len(all_rates)
        else:
            logger.warning("No rates obtained from any source.")
            return 0
