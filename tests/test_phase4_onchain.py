from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from onchain_alpha.data.phase4 import (
    lifecycle_censor_status,
    normalize_wallet_id,
    pool_identity,
    shrink_skill,
    temporal_edges_asof,
    wallet_state_asof,
)


def test_wallet_normalization_is_chain_aware():
    assert normalize_wallet_id("56", "0xAbC") == "56:0xabc"
    assert normalize_wallet_id("CT_501", "AbCd") == "CT_501:AbCd"


def test_pool_identity_does_not_collapse_missing_pool():
    assert pool_identity("56", "PancakeSwap", "0xPool") == "56:PancakeSwap:0xPool"
    assert pool_identity("56", "PancakeSwap", None) is None


def test_small_sample_skill_shrinkage_pulls_extreme_toward_prior():
    assert shrink_skill(5.0, 1, prior=0.0, prior_strength=5) == pytest.approx(5 / 6)
    assert abs(shrink_skill(5.0, 100, prior=0.0) - 5.0) < abs(shrink_skill(5.0, 1, prior=0.0) - 5.0)


def test_future_trade_cannot_change_historical_wallet_state():
    d = pd.DataFrame({"wallet_key": ["56:0xa", "56:0xa", "56:0xb"], "trade_id": ["1", "2", "3"], "asset_id": ["x", "x", "x"], "trade_time": pd.to_datetime(["2026-01-01T00:00Z", "2026-01-01T01:00Z", "2026-01-02T00:00Z"])})
    first = wallet_state_asof(d, "2026-01-01T01:00Z")
    appended = pd.concat([d, pd.DataFrame({"wallet_key": ["56:0xa"], "trade_id": ["4"], "asset_id": ["y"], "trade_time": pd.to_datetime(["2026-01-03T00:00Z"])})], ignore_index=True)
    second = wallet_state_asof(appended, "2026-01-01T01:00Z")
    pd.testing.assert_frame_equal(first, second)


def test_future_edge_cannot_change_temporal_graph_snapshot():
    e = pd.DataFrame({"wallet_id": ["a", "b"], "asset_id": ["x", "x"], "event_time": pd.to_datetime(["2026-01-01T00:00Z", "2026-01-02T00:00Z"])})
    snap = temporal_edges_asof(e, "2026-01-01T12:00Z")
    assert snap.wallet_id.tolist() == ["a"]


def test_lifecycle_right_censoring():
    assert lifecycle_censor_status("2026-01-01T00:00Z", "2026-01-01T01:00Z", "2026-01-01T02:00Z") == "RIGHT_CENSORED_ACTIVE"
    assert lifecycle_censor_status("2026-01-01T00:00Z", "2026-01-01T01:00Z", "2026-01-03T00:00Z") == "EVENT_INACTIVE"


def test_wallet_skill_gate_artifact_is_not_promoted_without_history(tmp_path: Path):
    from onchain_alpha.data.phase4 import run_wallet_skill
    (tmp_path / "artifacts").mkdir(parents=True)
    pd.DataFrame([{"status": "FAIL"}]).to_parquet(tmp_path / "artifacts/wallet_skill_gate.parquet", index=False)
    result = run_wallet_skill(tmp_path)
    assert result.iloc[0]["status"] == "BLOCKED_BY_SAMPLE"

