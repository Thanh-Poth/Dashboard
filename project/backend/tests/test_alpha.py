import polars as pl
import pytest
from features.alpha_primitive import add, div, mul, sub, ts_delay, ts_delta, ts_max, ts_mean, ts_min, ts_std


@pytest.fixture
def sample_df():
    return pl.DataFrame({
        "x": [10.0, 20.0, 30.0, 40.0],
        "y": [2.0, 0.0, 5.0, 10.0],
    })


def test_ts_delay(sample_df):
    result = sample_df.select(ts_delay(pl.col("x"), 1))["x"].to_list()
    assert result == [None, 10.0, 20.0, 30.0]


def test_ts_delta(sample_df):
    result = sample_df.select(ts_delta(pl.col("x"), 1))["x"].to_list()
    assert result == [None, 10.0, 10.0, 10.0]


def test_ts_mean(sample_df):
    result = sample_df.select(ts_mean(pl.col("x"), 2))["x"].to_list()
    assert result == [None, 15.0, 25.0, 35.0]


def test_ts_min_and_max(sample_df):
    res_max = sample_df.select(ts_max(pl.col("x"), 2))["x"].to_list()
    res_min = sample_df.select(ts_min(pl.col("x"), 2))["x"].to_list()
    assert res_max == [None, 20.0, 30.0, 40.0]
    assert res_min == [None, 10.0, 20.0, 30.0]


def test_div_handles_zero_safely(sample_df):
    # La deuxième ligne divise par y=0.0 : elle doit renvoyer x / 1e-8 sans lever d'exception[cite: 1]
    result = sample_df.select(div(pl.col("x"), pl.col("y")))["x"].to_list()
    assert result[0] == pytest.approx(5.0)
    assert result[1] == pytest.approx(20.0 / 1e-8)


def test_arithmetic_operators(sample_df):
    df_calc = sample_df.select(
        add(pl.col("x"), pl.col("y")).alias("sum"),
        sub(pl.col("x"), pl.col("y")).alias("diff"),
        mul(pl.col("x"), pl.col("y")).alias("prod"),
    )
    assert df_calc["sum"][0] == 12.0
    assert df_calc["diff"][0] == 8.0
    assert df_calc["prod"][0] == 20.0