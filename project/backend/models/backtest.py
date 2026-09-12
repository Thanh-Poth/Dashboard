import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital

    def run(self, df: pd.DataFrame, predictions: np.ndarray, price_col: str = 'Close', allow_short: bool = True) -> dict:
        """
        Exécute un backtest vectorisé basé sur les prédictions du modèle.
        """
        bt_df = df.copy()
        
        # Transformation des prédictions (qui sont 0 ou 1) en signaux de trading
        if allow_short:
            # 1 = Long (Achat), 0 = Short (Vente à découvert -> signal -1)
            bt_df['Signal'] = np.where(predictions == 0, -1, 1)
        else:
            # 1 = Long, 0 = Cash (hors du marché)
            bt_df['Signal'] = predictions
        
        # Rendement journalier de l'actif[cite: 4]
        bt_df['Market_Returns'] = bt_df[price_col].pct_change()
        
        # Rendement de la stratégie : on décale le signal d'un jour pour simuler
        # la prise de position à la clôture de t-1 pour le rendement du jour t.
        bt_df['Strategy_Returns'] = bt_df['Signal'].shift(1) * bt_df['Market_Returns']
        
        bt_df.dropna(inplace=True)
        
        # Calcul de la valeur du portefeuille
        bt_df['Portfolio_Value'] = self.initial_capital * (1 + bt_df['Strategy_Returns']).cumprod()
        bt_df['Buy_Hold_Value'] = self.initial_capital * (1 + bt_df['Market_Returns']).cumprod()

        # --- CALCUL DES MÉTRIQUES ---
        total_return = (bt_df['Portfolio_Value'].iloc[-1] / self.initial_capital) - 1
        market_return = (bt_df['Buy_Hold_Value'].iloc[-1] / self.initial_capital) - 1
        
        days = len(bt_df)
        annualized_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0
        
        volatility = bt_df['Strategy_Returns'].std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility != 0 else 0
        
        cumulative_returns = (1 + bt_df['Strategy_Returns']).cumprod()
        peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min()

        results = {
            'Data': bt_df,
            'Total_Return': total_return,
            'Market_Return': market_return,
            'Annualized_Return': annualized_return,
            'Sharpe_Ratio': sharpe_ratio,
            'Max_Drawdown': max_drawdown
        }
        
        return results