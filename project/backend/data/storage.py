import logging
import pandas as pd

logger = logging.getLogger(__name__)

class DataStorage:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def save_as_parquet(self, df: pd.DataFrame, ticker: str):
        if df.empty or not ticker:
            return

        file_path = f"{self.base_path}/{ticker}_data.parquet"
        df.to_parquet(file_path, engine='pyarrow')
        logger.info(f"Data saved in {file_path}")

    def save_as_csv(self, df: pd.DataFrame, ticker: str):
        if df.empty or not ticker:
            return

        file_path = f"{self.base_path}/{ticker}_data.csv"
        df.to_csv(file_path)
        logger.info(f"Data saved in {file_path}")