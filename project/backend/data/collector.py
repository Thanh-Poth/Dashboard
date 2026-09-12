from abc import ABC, abstractmethod
from datetime import datetime
import logging
import MetaTrader5 as mt5
import pandas as pd
import pytz
import yfinance as yf

logger = logging.getLogger(__name__)


class BaseDataCollector(ABC):
    def __init__(self, ticker: str, start_date: str, end_date: str):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date

    @abstractmethod
    def collect_data(self) -> pd.DataFrame:
        """Récupère les données historiques sous forme de DataFrame standardisé."""
        pass

    def validate_data(self, df: pd.DataFrame) -> bool:
        return not df.empty


class YahooFinanceCollector(BaseDataCollector):
    def collect_data(self) -> pd.DataFrame:
        logger.info(f"Downloading data for {self.ticker} from {self.start_date} to {self.end_date}")
        df = yf.download(self.ticker, start=self.start_date, end=self.end_date)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel('Ticker')

        df.index.name = 'Date'
        df.columns.name = None

        logger.info(f"Successfully downloaded data from {self.ticker}")
        return df


class MT5Collector(BaseDataCollector):
    def collect_data(self) -> pd.DataFrame:
        logger.info(f"Downloading data for {self.ticker} from {self.start_date} to {self.end_date} via MT5")

        if not mt5.initialize():
            logger.error(f"Échec de l'initialisation MT5, code d'erreur = {mt5.last_error()}")
            return pd.DataFrame()

        if not mt5.symbol_select(self.ticker, True):
            logger.error(f"Le symbole {self.ticker} n'a pas pu être trouvé dans MT5.")
            mt5.shutdown()
            return pd.DataFrame()

        timezone = pytz.timezone("UTC")
        start = pd.to_datetime(self.start_date)
        end = pd.to_datetime(self.end_date)

        utc_start = datetime(start.year, start.month, start.day, tzinfo=timezone)
        utc_end = datetime(end.year, end.month, end.day, tzinfo=timezone)

        rates = mt5.copy_rates_range(self.ticker, mt5.TIMEFRAME_D1, utc_start, utc_end)
        mt5.shutdown()

        if rates is None or len(rates) == 0:
            logger.warning(f"Aucune donnée récupérée pour {self.ticker} sur MT5.")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        df = df.rename(columns={
            'time': 'Date', 'open': 'Open', 'high': 'High',
            'low': 'Low', 'close': 'Close', 'tick_volume': 'Volume'
        })

        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        df.set_index('Date', inplace=True)

        logger.info(f"Successfully downloaded data from {self.ticker} via MT5")
        return df


COLLECTOR_REGISTRY: dict[str, type[BaseDataCollector]] = {
    "yahoo": YahooFinanceCollector,
    "mt5": MT5Collector,
}


def get_collector(source: str, ticker: str, start_date: str, end_date: str) -> BaseDataCollector:
    collector_cls = COLLECTOR_REGISTRY.get(source.strip().lower())
    if not collector_cls:
        raise ValueError(
            f"Source inconnue : « {source} ». Sources valides : {list(COLLECTOR_REGISTRY.keys())}"
        )
    return collector_cls(ticker=ticker, start_date=start_date, end_date=end_date)