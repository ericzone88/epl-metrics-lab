import pandas as pd
import numpy as np
from player_analyzer import ForwardScorer

dummy_df = pd.DataFrame({"fake": [1, 2, 3]})

def test_normalize_method():
    scorer = ForwardScorer(dummy_df)
    series = pd.Series([0, 5, 10])
    result = scorer.normalize(series)
    expected = pd.Series([0.0, 0.5, 1.0])
    pd.testing.assert_series_equal(result, expected)

def test_log_scaling_method():
    scorer = ForwardScorer(dummy_df)
    series = pd.Series([0, 9, 99])
    log_scaled = np.log1p(series)
    expected = scorer.normalize(log_scaled)
    result = scorer.log_scaling(series)
    pd.testing.assert_series_equal(result, expected)

def test_smart_scale_no_outliers():
    df = pd.DataFrame({"x": [10, 20, 30, 40, 50]})
    scorer = ForwardScorer(df.copy())
    result_df = scorer.smart_scale(df.copy(), "x")
    expected = scorer.normalize(df["x"])
    actual = result_df["x_norm"]
    pd.testing.assert_series_equal(actual, expected, check_names=False)

def test_smart_scale_with_outliers():
    df = pd.DataFrame({"x": [10, 20, 30, 40, 1000]})
    scorer = ForwardScorer(df.copy())
    result_df = scorer.smart_scale(df.copy(), "x")
    log_scaled = np.log1p(df["x"])
    expected = scorer.normalize(log_scaled)
    actual = result_df["x_norm"]
    pd.testing.assert_series_equal(actual, expected, check_names=False)