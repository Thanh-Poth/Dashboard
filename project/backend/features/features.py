import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class Features:
    def __init__(self,
                df : pd.DataFrame):
        
        self.df = df


    def days(self) -> pd.DataFrame:
        self.df['Weekdays'] = pd.to_datetime(self.df['Date']).dt.weekday
        self.df["Month"] = pd.to_datetime(self.df['Date']).dt.month
        self.df["Trimestre"] = pd.to_datetime(self.df['Date']).dt.quarter
        return self.df

    def end_period(self) -> pd.DataFrame:

        self.df['fin_de_mois'] = pd.to_datetime(self.df['Date']).dt.is_month_end
        self.df['fin_de_trimestre'] = pd.to_datetime(self.df['Date']).dt.is_quarter_end
        self.df['fin_d_annee'] = pd.to_datetime(self.df['Date']).dt.is_year_end
        return self.df

    def deltaHL(self) -> pd.DataFrame:
        self.df["delta_HL"] = self.df['High'] - self.df['Low']
        return self.df

    def deltaHC(self) -> pd.DataFrame:
        self.df["delta_HC"] = self.df['High'] - self.df['Close']
        return self.df

    def deltaOC(self) -> pd.DataFrame:
        self.df["delta_OC"] = self.df['Open'] - self.df['Close']
        return self.df

    def deltaOH(self) -> pd.DataFrame:
        self.df["delta_OH"] = self.df['Open'] - self.df['High']
        return self.df

    def deltaOL(self) -> pd.DataFrame:
        self.df["delta_OL"] = self.df['Open'] - self.df['Low']
        return self.df

    def deltaCH(self) -> pd.DataFrame:
        self.df["delta_CH"] = self.df['Close'] - self.df['High']
        return self.df

    def deltaCL(self) -> pd.DataFrame:
        self.df["delta_CL"] = self.df['Close'] - self.df['Low']
        return self.df

    def simple_return(self) -> pd.DataFrame:
        self.df['Simple_Returns'] = (self.df['Close'] / self.df['Close'].shift(1)) - 1
        logger.debug("Colonne 'Simple_Returns' calculée.")
        return self.df

    def log_return(self) -> pd.DataFrame:
        self.df['Log_Returns'] = np.log(self.df['Close'] / self.df['Close'].shift(1))
        logger.debug("Colonne 'Log_Returns' calculée.")
        return self.df

    def distance_SMA_k(self, k : int) -> pd.DataFrame:
        self.df[f'SMA_{k}'] = self.df['Close'].rolling(window=k).mean()
        self.df[f'Distance_SMA_{k}'] = (self.df['Close'] - self.df[f'SMA_{k}']) / self.df[f'SMA_{k}']
        return self.df

    def volatility(self, N : int) -> pd.DataFrame:
        self.df['Returns'] = self.df['Close'].pct_change()
        self.df['Rolling_volatility'] = self.df['Returns'].rolling(window=N).std()
        return self.df

    def Zscore(self, N : int) -> pd.DataFrame:
        self.df['Rolling_mean'] = self.df['Close'].rolling(window=N).mean()
        self.df['std_deviation'] = self.df['Close'].rolling(window=N).std()
        self.df['Z_Score'] = (self.df['Close'] - self.df['Rolling_mean']) / self.df['std_deviation']
        return self.df

    def RSI(self, N : int) -> pd.DataFrame:
        delta = self.df['Close'].diff()
        gains = delta.where(delta > 0, 0)
        pertes = -delta.where(delta < 0, 0)

        moyenne_gains = gains.ewm(alpha=1/N, adjust=False).mean()
        moyenne_pertes = pertes.ewm(alpha=1/N, adjust=False).mean()

        rs = moyenne_gains / moyenne_pertes

        self.df['RSI'] = 100 - (100 / (1 + rs))
        return self.df

    def MACD(self, N1 : int, N2 : int) -> pd.DataFrame:
        self.df['EMA_12'] = self.df['Close'].ewm(span=12, adjust=False).mean()
        self.df['EMA_26'] = self.df['Close'].ewm(span=26, adjust=False).mean()
        self.df['MACD'] = self.df['EMA_12'] - self.df['EMA_26']
        return self.df

    def On_balance_volume(self ) -> pd.DataFrame:
        variation_prix = self.df['Close'].diff()
        direction = np.sign(variation_prix)
        direction = direction.fillna(0)

        volume_ajuste = direction * self.df['Volume']
        self.df['OBV'] = volume_ajuste.cumsum()
        return self.df

    def OC(self ):
        self.df["OC"] = np.where(self.df["Open"] - self.df["Close"] < 0, 1, 0)
        self.df["OC"] = self.df["OC"].shift(-1)
        
        return self.df

    def clean(self):
        self.df = self.df.select_dtypes(include=[np.number])
        df_clean = self.df.replace([np.inf, -np.inf], np.nan)
        df_clean = df_clean.dropna()
        return df_clean

    def daily_return(self) -> pd.DataFrame:
        self.df['Daily_Return'] = self.df['Close'].pct_change() * 100
        return self.df

    def add_features (self) :
        self.days()
        self.end_period()
        self.deltaHL()
        self.deltaHC()
        self.deltaOC()
        self.deltaOH()
        self.deltaOL()
        self.deltaCH()
        self.deltaCL()
        self.simple_return()
        self.log_return()
        self.daily_return()
        self.distance_SMA_k(k = 12)   
        self.volatility(N = 16)
        self.Zscore(N = 12)
        self.RSI(N = 14)
        self.MACD(N1 = 12, N2 = 24)
        self.On_balance_volume()
        self.OC()
        return self.df