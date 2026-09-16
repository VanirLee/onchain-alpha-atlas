from __future__ import annotations

import numpy as np
import pandas as pd
import sqlite3
from statsmodels.stats.multitest import multipletests

from onchain_alpha.data.canonical import build_fact_token_market_state
from onchain_alpha.connectors.local_sqlite import LocalSQLiteReadOnlyAdapter
from onchain_alpha.entities.skill.engine import blocked_wallet_result, build_wallet_skill_history
from onchain_alpha.events.detectors import detect_volume_shock
from onchain_alpha.features.core import build_factor_panel
from onchain_alpha.hypotheses.registry import load_hypothesis
from onchain_alpha.labels.forward_returns import build_forward_labels
from onchain_alpha.research.event_study.engine import run_event_study
from onchain_alpha.research.network.temporal import asof_graph_edges
from onchain_alpha.research.state.conditional import run_state_conditional_event_study
from onchain_alpha.screening.ic import summarize_ic
from onchain_alpha.stats.multiple_testing import benjamini_hochberg
from onchain_alpha.stats.robustness import split_ic


def _market_rows(times: list[str], *, chain: str = "BSC", token: str = "0x1", prices: list[float] | None = None) -> pd.DataFrame:
    prices = prices or [100.0 + i for i in range(len(times))]
    return pd.DataFrame({
        "chain": chain,
        "token_address": token,
        "event_time": pd.to_datetime(times, utc=True),
        "observed_at": pd.to_datetime(times, utc=True),
        "price": prices,
        "volume": np.arange(1, len(times) + 1, dtype=float),
        "liquidity": np.full(len(times), 1_000.0),
        "market_cap": np.full(len(times), 10_000.0),
    })


def test_bh_exact_values_and_statsmodels_agree() -> None:
    raw = [0.001, 0.02, 0.5]
    got = [row["fdr_adjusted_p_value"] for row in benjamini_hochberg(raw)]
    expected = multipletests(raw, method="fdr_bh")[1]
    assert np.allclose(got, [0.003, 0.03, 0.5])
    assert np.allclose(got, expected)
    assert all(adjusted >= raw_p for adjusted, raw_p in zip(got, raw))


def test_ic_p_value_tests_mean_time_series_ic_not_mean_cross_sectional_pvalues() -> None:
    result = summarize_ic([0.2, 0.3, 0.25, 0.1, 0.15, 0.2], horizon=4)
    assert result["n_periods"] == 6
    assert result["t_stat"] is not None
    assert result["naive_p_value"] is not None
    assert result["HAC_t_stat"] is not None
    assert result["HAC_p_value"] is not None
    assert result["HAC_lag"] == 4
    assert result["raw_p_value"] == result["HAC_p_value"]


def test_irregular_timestamp_does_not_create_row_position_horizon() -> None:
    rows = _market_rows([
        "2025-01-01 00:00", "2025-01-01 01:00", "2025-01-01 02:00", "2025-01-01 03:00",
        "2025-01-01 04:00", "2025-01-01 05:00", "2025-01-01 06:00", "2025-01-01 07:00",
        "2025-01-01 08:00", "2025-01-01 09:00", "2025-01-01 10:00", "2025-01-01 11:00",
        "2025-01-01 12:00", "2025-01-01 13:00", "2025-01-01 14:00", "2025-01-01 15:00",
        "2025-01-01 16:00", "2025-01-01 17:00", "2025-01-01 18:00", "2025-01-01 19:00",
        "2025-01-01 20:00", "2025-01-01 21:00", "2025-01-01 22:00", "2025-01-01 23:00",
        "2025-01-02 00:00", "2025-01-02 01:00",
    ])
    rows = rows[~rows["event_time"].isin([
        pd.Timestamp("2025-01-01 05:00", tz="UTC"),
        pd.Timestamp("2025-01-02 01:00", tz="UTC"),
    ])]
    labels = build_forward_labels(rows, horizons=(24,))
    at_zero = labels.loc[labels["feature_time"] == pd.Timestamp("2025-01-01 00:00", tz="UTC")].iloc[0]
    at_one = labels.loc[labels["feature_time"] == pd.Timestamp("2025-01-01 01:00", tz="UTC")].iloc[0]
    assert np.isfinite(at_zero["forward_return_24h"])
    assert pd.isna(at_one["forward_return_24h"])


def test_features_are_invariant_when_future_data_is_appended() -> None:
    base = _market_rows(pd.date_range("2025-01-01", periods=30, freq="h").astype(str).tolist())
    future = _market_rows(pd.date_range("2025-01-02 06:00", periods=8, freq="h").astype(str).tolist(), prices=[200 + i for i in range(8)])
    future["volume"] = 10_000.0
    through_t = build_factor_panel(base)
    appended = build_factor_panel(pd.concat([base, future], ignore_index=True))
    cols = ["feature_time", "chain", "token_address", "chain_volume_breadth", "market_vol_regime"]
    left = through_t[cols].sort_values("feature_time").reset_index(drop=True)
    right = appended[appended["feature_time"] <= base["event_time"].max()][cols].sort_values("feature_time").reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right, check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12)


def test_neutralized_factor_is_orthogonal_to_controls() -> None:
    rows = []
    for ts in pd.date_range("2025-01-01", periods=3, freq="h", tz="UTC"):
        for i in range(8):
            rows.append({"chain": "BSC", "token_address": f"0x{i}", "event_time": ts, "observed_at": ts, "price": 100 + i + ts.hour, "volume": 100 + i, "liquidity": 1_000 + i * 50, "market_cap": 10_000 + i * 700})
    panel = build_factor_panel(pd.DataFrame(rows))
    valid = panel[["momentum_1h_neutralized", "log_market_cap", "log_liquidity", "volatility"]].dropna()
    assert not valid.empty
    assert abs(valid["momentum_1h_neutralized"].corr(valid["log_market_cap"])) < 1e-8
    assert abs(valid["momentum_1h_neutralized"].corr(valid["log_liquidity"])) < 1e-8


def test_oos_purges_train_labels_touching_test_start_and_uses_timestamp_ic() -> None:
    times = pd.date_range("2025-01-01", periods=20, freq="h", tz="UTC")
    obs = []
    for ts in times:
        for i in range(6):
            obs.append({"chain": "BSC", "token_address": f"0x{i}", "event_time": ts, "observed_at": ts, "price": 100 + i + ts.hour, "volume": 100 + i, "liquidity": 1_000 + i, "market_cap": 10_000 + i})
    obs = pd.DataFrame(obs)
    panel = build_factor_panel(obs)
    labels = build_forward_labels(obs, horizons=(4,))
    result = split_ic(panel, labels, factor="momentum_1h", horizon=4)
    test = result[result["split"] == "test_oos"].iloc[0]
    train = result[result["split"] == "train"].iloc[0]
    assert train["train_end"] < test["test_start"]
    assert train["embargo_hours"] == 4
    assert "HAC_p_value" in result.columns
    assert test["n_timestamps"] <= len(times)


def test_event_study_uses_exact_target_time_and_reports_real_result() -> None:
    times = pd.date_range("2025-01-01", periods=30, freq="h", tz="UTC")
    state = build_fact_token_market_state(_market_rows([t.isoformat() for t in times]))
    events = pd.DataFrame([{"event_id": "e1", "event_type": "volume_shock", "asset_id": "BSC:0x1", "chain": "BSC", "event_time": times[0], "available_time": times[0]}])
    result = run_event_study(events, state, horizons=(24,), n_bootstrap=50)
    assert result.iloc[0]["status"] == "EXPLORATORY"
    assert result.iloc[0]["n_events"] == 1


def test_state_conditional_study_uses_pre_event_state_only() -> None:
    times = pd.date_range("2025-01-01", periods=36, freq="h", tz="UTC")
    state = build_fact_token_market_state(_market_rows([t.isoformat() for t in times]))
    events = pd.DataFrame([{"event_id": "e1", "event_type": "volume_shock", "asset_id": "BSC:0x1", "chain": "BSC", "event_time": times[5], "available_time": times[5]}])
    result = run_state_conditional_event_study(events, state, horizons=(1,))
    assert set(["state_variable", "state_bucket", "mean_return", "status"]).issubset(result.columns)


def test_local_sqlite_adapter_is_read_only(tmp_path) -> None:
    path = tmp_path / "local.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE candles (id INTEGER, candle_ts_ms INTEGER)")
        conn.execute("INSERT INTO candles VALUES (1, 1000)")
        conn.commit()
    adapter = LocalSQLiteReadOnlyAdapter(path)
    assert adapter.tables() == ["candles"]
    assert len(adapter.read("candles")) == 1
    assert adapter.summary()["read_only"] is True


def test_wallet_skill_excludes_future_closed_trade_and_blocks_missing_real_panel() -> None:
    trades = pd.DataFrame([
        {"wallet_id": "w1", "exit_time": "2025-01-01T01:00Z", "available_time": "2025-01-01T02:00Z", "realized_return": 0.1},
        {"wallet_id": "w1", "exit_time": "2025-01-01T03:00Z", "available_time": "2025-01-01T04:00Z", "realized_return": -0.1},
        {"wallet_id": "w1", "exit_time": "2025-01-01T05:00Z", "available_time": "2025-01-01T06:00Z", "realized_return": 0.2},
    ])
    result = build_wallet_skill_history(trades, [pd.Timestamp("2025-01-01T05:30Z")], min_trades=2)
    assert result.iloc[0]["closed_trade_count"] == 2
    assert result.iloc[0]["status"] == "COMPUTED"
    assert blocked_wallet_result().iloc[0]["status"] == "BLOCKED_BY_DATA"


def test_temporal_graph_snapshot_excludes_future_edges_and_preserves_asset_identity() -> None:
    edges = pd.DataFrame([
        {"source": "w", "target": "BSC:0x1", "event_time": "2025-01-01T00:00Z", "available_time": "2025-01-01T00:00Z"},
        {"source": "w", "target": "BASE:0x1", "event_time": "2025-01-02T00:00Z", "available_time": "2025-01-02T00:00Z"},
    ])
    snapshot = asof_graph_edges(edges, pd.Timestamp("2025-01-01T12:00Z"))
    assert len(snapshot) == 1
    assert snapshot.iloc[0]["target"] == "BSC:0x1"


def test_event_detector_does_not_change_past_when_future_volume_is_appended() -> None:
    times = pd.date_range("2025-01-01", periods=20, freq="h", tz="UTC")
    base = _market_rows([t.isoformat() for t in times])
    base.loc[base.index[-1], "volume"] = 10_000
    extended = pd.concat([base, _market_rows(["2025-01-01T20:00Z", "2025-01-01T21:00Z"], prices=[120, 121])], ignore_index=True)
    extended.loc[extended.index[-2:], "volume"] = 20_000
    old = detect_volume_shock(build_fact_token_market_state(base), min_history=5)
    new = detect_volume_shock(build_fact_token_market_state(extended), min_history=5)
    old_ids = set(old.loc[old["event_time"] <= times[-1], "event_id"])
    new_ids = set(new.loc[new["event_time"] <= times[-1], "event_id"])
    assert old_ids == new_ids


def test_hypothesis_registry_loads_first_class_yaml() -> None:
    hypothesis = load_hypothesis(__import__("pathlib").Path(__file__).parents[1], "H001")
    assert hypothesis.family == "event_response"
    assert hypothesis.classification == "EXPLORATORY"
