import numpy as np
import pandas as pd
import pytest
from models.backtest import Backtester


def test_strategy_returns_lookahead_bias():
    # Prix : 100 -> 110 (+10%), puis 110 -> 88 (-20%)
    df = pd.DataFrame({"Close": [100.0, 110.0, 88.0]})
    # Signal généré en t=0 (1) et t=1 (0 -> -1 en short)[cite: 2]
    predictions = np.array([1, 0, 0])

    bt = Backtester(initial_capital=1000.0)
    res = bt.run(df, predictions, allow_short=True)

    # t=1 : Signal(t=0) * Ret(t=1) = 1 * (+0.10) = +0.10[cite: 2]
    # t=2 : Signal(t=1) * Ret(t=2) = -1 * (-0.20) = +0.20[cite: 2]
    strategy_returns = res["Data"]["Strategy_Returns"].tolist()
    assert strategy_returns == pytest.approx([0.10, 0.20])


def test_allow_short_logic():
    df = pd.DataFrame({"Close": [100.0, 80.0]})  # Baisse de 20%
    predictions = np.array([0, 0])
    bt = Backtester(initial_capital=1000.0)

    # Mode Short : signal -1 sur un marché à -20% génère +20% de gain[cite: 2]
    res_short = bt.run(df, predictions, allow_short=True)
    assert res_short["Total_Return"] == pytest.approx(0.20)

    # Mode Long/Cash : signal 0 protège le capital (gain nul)[cite: 2]
    res_cash = bt.run(df, predictions, allow_short=False)
    assert res_cash["Total_Return"] == pytest.approx(0.0)


def test_max_drawdown():
    # Parcours : 100 -> 200 (+100%) -> 100 (-50%) -> 150 (+50%)
    # Le pire creux part du pic de 200 à 100, soit un drawdown de -50%
    df = pd.DataFrame({"Close": [100.0, 200.0, 100.0, 150.0]})
    predictions = np.array([1, 1, 1, 1])

    bt = Backtester(initial_capital=100.0)
    res = bt.run(df, predictions, allow_short=False)

    assert res["Max_Drawdown"] == pytest.approx(-0.50)


def test_zero_volatility_sharpe():
    # Cours stable : volatilité nulle, le Sharpe doit renvoyer 0 sans ZeroDivisionError[cite: 2]
    df = pd.DataFrame({"Close": [100.0, 100.0, 100.0, 100.0]})
    predictions = np.array([1, 1, 1, 1])

    bt = Backtester(initial_capital=1000.0)
    res = bt.run(df, predictions)

    assert res["Sharpe_Ratio"] == 0.0
    assert res["Total_Return"] == pytest.approx(0.0)