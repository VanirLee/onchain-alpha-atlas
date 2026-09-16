import numpy as np
import pandas as pd
import pytest
from scipy.stats import t as student_t
from statsmodels.stats.multitest import multipletests

from onchain_alpha.backtest.engine import asset_key, run_backtest
from onchain_alpha.features.core import FACTOR_NAMES, _residualize_by_timestamp, build_factor_panel
from onchain_alpha.labels import build_forward_labels
from onchain_alpha.screening.ic import cross_sectional_ic_series, rank_ic, summarize_ic
from onchain_alpha.stats.multiple_testing import benjamini_hochberg
from onchain_alpha.stats.robustness import split_ic


def _observations(start="2026-01-01T00:00:00Z", hours=60, tokens=6):
    start = pd.Timestamp(start, tz="UTC")
    rows = []
    for i in range(tokens):
        token = f"T{i}"
        for h in range(hours):
            ts = start + pd.Timedelta(hours=h)
            rows.append({
                "chain": "56", "token_address": token, "event_time": ts.isoformat(), "observed_at": (ts + pd.Timedelta(minutes=1)).isoformat(),
                "price": 100 + i * 10 + h * (1 + i / 20), "volume": 1000 + i * 100 + h, "liquidity": 50000 + i * 700 + h * 3,
                "market_cap": 100000 + i * 5000 + h * 11, "holders": 100 + i * 5 + h, "buy_volume": 600 + i, "sell_volume": 400,
            })
    return pd.DataFrame(rows)


def test_bh_exact_values_and_statsmodels_crosscheck():
    raw = [0.001, 0.02, 0.5]
    got = [x["fdr_adjusted_p_value"] for x in benjamini_hochberg(raw)]
    expected = multipletests(raw, method="fdr_bh")[1].tolist()
    assert got == pytest.approx(expected)
    assert got == pytest.approx([0.003, 0.03, 0.5])
    assert all(adjusted >= value for adjusted, value in zip(got, raw))

def test_ic_inference_tests_mean_ic_not_mean_cross_sectional_pvalues():
    rows = []
    for t in range(8):
        ts = pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=t)
        for i in range(10):
            target_rank = [0, 2, 1, 4, 3, 5, 7, 6, 9, 8][(i + t) % 10]
            rows.append({"chain": "56", "token_address": f"T{i}", "feature_time": ts, "factor": i + (t % 3) * 0.01, "target": target_rank * 0.02 + (t - 3) * 0.01})
    frame = pd.DataFrame(rows)
    series = cross_sectional_ic_series(frame, "factor", "target")
    summary = summarize_ic(series["ic"].tolist(), horizon=4)
    t_stat = summary["mean_ic"] / (summary["ic_std"] / np.sqrt(summary["n_periods"]))
    assert summary["t_stat"] == pytest.approx(t_stat)
    assert summary["naive_p_value"] == pytest.approx(2 * student_t.sf(abs(t_stat), summary["n_periods"] - 1))
    assert summary["HAC_lag"] == 4
    assert summary["raw_p_value"] == summary["HAC_p_value"]
    ic_summary, _ = rank_ic(frame.rename(columns={"factor": "momentum_1h"}).assign(momentum_1h_rank=0), frame.rename(columns={"target": "forward_return_4h"}))
    assert "HAC_p_value" in ic_summary.columns
    assert "p_value" not in ic_summary.columns or not ic_summary["p_value"].equals(ic_summary["raw_p_value"])


def test_irregular_timestamp_targets_require_exact_clock_time():
    obs = _observations(hours=30, tokens=1)
    obs["event_time"] = pd.to_datetime(obs["event_time"], utc=True)
    obs = obs[~obs["event_time"].isin([obs.iloc[i]["event_time"] for i in range(3, 25)])].copy()
    labels = build_forward_labels(obs)
    t0 = pd.Timestamp("2026-01-01T00:00:00Z")
    row0 = labels[labels["feature_time"] == t0].iloc[0]
    assert pd.isna(row0["forward_return_24h"])
    row1 = labels[labels["feature_time"] == t0 + pd.Timedelta(hours=1)].iloc[0]
    assert row1["exit_time_24h"] == t0 + pd.Timedelta(hours=25)
    panel = build_factor_panel(obs)
    row25 = panel[panel["feature_time"] == t0 + pd.Timedelta(hours=25)].iloc[0]
    price_at_25 = float(obs.loc[pd.to_datetime(obs["event_time"], utc=True) == t0 + pd.Timedelta(hours=25), "price"].iloc[0])
    price_at_1 = float(obs.loc[pd.to_datetime(obs["event_time"], utc=True) == t0 + pd.Timedelta(hours=1), "price"].iloc[0])
    assert row25["momentum_24h"] == pytest.approx(price_at_25 / price_at_1 - 1)


def test_features_are_invariant_to_appended_future_data():
    base = _observations(hours=40)
    future = _observations(start="2026-01-02T16:00:00Z", hours=8)
    base_panel = build_factor_panel(base)
    appended_panel = build_factor_panel(pd.concat([base, future], ignore_index=True))
    cols = ["chain", "token_address", "feature_time", *FACTOR_NAMES, "log_market_cap", "log_liquidity", "volatility"]
    left = base_panel[base_panel["feature_time"] <= pd.Timestamp("2026-01-02T15:00:00Z")][cols].sort_values(["chain", "token_address", "feature_time"]).reset_index(drop=True)
    right = appended_panel[appended_panel["feature_time"] <= pd.Timestamp("2026-01-02T15:00:00Z")][cols].sort_values(["chain", "token_address", "feature_time"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right, check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12)


def test_neutralization_residual_is_orthogonal_to_controls():
    idx = pd.RangeIndex(8)
    times = pd.Series([pd.Timestamp("2026-01-01", tz="UTC")] * 8, index=idx)
    controls = pd.DataFrame({"log_market_cap": np.arange(8, dtype=float), "log_liquidity": np.arange(8, dtype=float) ** 2, "volatility": [0.1, 0.4, 0.2, 0.8, 0.3, 0.7, 0.5, 0.9]}, index=idx)
    factor = 2 * controls["log_market_cap"] - 0.5 * controls["log_liquidity"] + 3 * controls["volatility"] + np.array([0, 1, -1, 2, -2, 1, -1, 0], dtype=float)
    residual = _residualize_by_timestamp(factor, controls, times)
    use = pd.concat([residual.rename("resid"), controls], axis=1).dropna()
    assert all(abs(use["resid"].corr(use[col])) < 1e-9 for col in controls.columns)


def _panel_labels(hours=72, tokens=6):
    obs = _observations(hours=hours, tokens=tokens)
    panel = build_factor_panel(obs)
    labels = build_forward_labels(obs)
    return panel, labels


def test_oos_is_timestamp_cross_sectional_and_purged():
    panel, labels = _panel_labels(hours=120)
    result = split_ic(panel, labels, factor="momentum_1h", horizon=24)
    assert set(result["split"]) == {"train", "test_oos"}
    train = result[result["split"] == "train"].iloc[0]
    test = result[result["split"] == "test_oos"].iloc[0]
    assert train["n_timestamps"] > 0 and test["n_timestamps"] > 0
    assert pd.Timestamp(train["train_end"]) + pd.Timedelta(hours=24) < pd.Timestamp(test["test_start"])
    assert "HAC_p_value" in result.columns and train["n_observations"] >= train["n_timestamps"] * 5


def test_cross_sectional_oos_not_pooled_token_timestamp_spearman():
    panel, labels = _panel_labels(hours=120)
    result = split_ic(panel, labels, factor="momentum_1h", horizon=24)
    test = result[result["split"] == "test_oos"].iloc[0]
    assert test["n_timestamps"] > 1
    assert test["n_observations"] >= test["n_timestamps"] * 5
    assert test["n_observations"] < len(panel)


def test_non_overlapping_backtest_accounting_and_no_capacity_claim():
    panel, labels = _panel_labels(hours=72)
    result = run_backtest(panel, labels, factor="momentum_1h", horizon=24)
    assert set(result["accounting_method"]) == {"non_overlapping_rebalance"}
    assert result["n_rebalances"].max() <= 3
    assert "capacity_proxy" not in result.columns
    assert set(result["capacity_status"]) == {"NOT_AVAILABLE_NO_EXECUTABLE_DEPTH"}


def test_asset_identity_includes_chain_and_token():
    frame = pd.DataFrame({"chain": ["56", "1", "56"], "token_address": ["SAME", "SAME", "SAME"]})
    keys = asset_key(frame)
    assert len(keys.unique()) == 2
    assert len(pd.Index(frame["token_address"]).unique()) == 1
