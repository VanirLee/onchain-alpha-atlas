from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from onchain_alpha.data.phase3 import (
    BinanceCEXReadOnly,
    backward_asof_join,
    build_asset_identity,
    build_dex_bars,
    build_independent_event_episodes,
    write_phase3_research_outputs,
)


def test_asset_mapping_never_pairs_symbol_only(tmp_path: Path):
    (tmp_path / "data/gold").mkdir(parents=True)
    pd.DataFrame([{"chain": "56", "token_address": "0xabc", "symbol": "BTC", "first_seen": "2026-01-01", "last_seen": "2026-01-02"}]).to_parquet(tmp_path / "data/gold/universe.parquet", index=False)
    (tmp_path / "data/silver/cex").mkdir(parents=True)
    pd.DataFrame([{"asset_id": "cex:BTC", "symbol": "BTCUSDT", "market_type": "SPOT", "event_time": pd.Timestamp("2026-01-01", tz="UTC"), "close": 1.0}]).to_parquet(tmp_path / "data/silver/cex/market_bars_5m.parquet", index=False)
    identity, counts = build_asset_identity(tmp_path)
    assert counts["DEX_CEX_PAIRED"] == 0
    assert identity.loc[identity.chain.notna(), "mapping_type"].eq("NO_CEX_MARKET").all()


def test_symbol_collision_is_not_an_exact_map(tmp_path: Path):
    test_asset_mapping_never_pairs_symbol_only(tmp_path)
    identity = pd.read_parquet(tmp_path / "data/gold/identity/asset_identity.parquet")
    assert identity[identity.chain.notna()].spot_symbol.isna().all()


def test_backward_asof_rejects_future_available_and_uses_past():
    left = pd.DataFrame({"asset_id": ["a", "a"], "timestamp": pd.to_datetime(["2026-01-01 00:05Z", "2026-01-01 00:15Z"])})
    right = pd.DataFrame({"asset_id": ["a", "a"], "timestamp": pd.to_datetime(["2026-01-01 00:00Z", "2026-01-01 00:10Z"]), "available_time": pd.to_datetime(["2026-01-01 00:01Z", "2026-01-01 00:11Z"]), "value": [1, 2]})
    out = backward_asof_join(left, right)
    assert out.value.tolist() == [1, 2]
    right.loc[1, "available_time"] = pd.Timestamp("2026-01-01 00:16Z")
    with pytest.raises(ValueError):
        backward_asof_join(left, right)


def test_missing_trade_is_not_zero_and_observed_trade_can_be_zero(tmp_path: Path):
    (tmp_path / "data/gold/trades").mkdir(parents=True)
    pd.DataFrame([{"trade_id": "1", "asset_id": "56:0x1", "chain": "56", "token_address": "0x1", "trade_time": "2026-01-01T00:01Z", "available_time": "2026-01-01T00:02Z", "side": "buy", "quantity": 1, "usd_value": 0.0, "price": 2.0, "wallet_id": None}]).to_parquet(tmp_path / "data/gold/trades/fact_wallet_trade.parquet", index=False)
    bars = build_dex_bars(tmp_path)
    assert len(bars) == 1
    assert bars.loc[0, "buy_volume"] == 0.0
    assert bars.loc[0, "source_status"] == "OBSERVED"


def test_dex_trade_dedup_by_identity(tmp_path: Path):
    (tmp_path / "data/gold/trades").mkdir(parents=True)
    row = {"trade_id": "same", "asset_id": "56:0x1", "chain": "56", "token_address": "0x1", "trade_time": "2026-01-01T00:01Z", "available_time": "2026-01-01T00:02Z", "side": "buy", "quantity": 1, "usd_value": 3.0, "price": 2.0, "wallet_id": None}
    pd.DataFrame([row, row]).drop_duplicates(["trade_id", "asset_id"]).to_parquet(tmp_path / "data/gold/trades/fact_wallet_trade.parquet", index=False)
    assert len(build_dex_bars(tmp_path)) == 1


def test_cex_allowlist_is_read_only():
    api = BinanceCEXReadOnly()
    with pytest.raises(ValueError):
        api.get("orders", {})
    api.close()


def test_local_checkpoint_raw_is_immutable(tmp_path: Path):
    from onchain_alpha.data.phase3 import _write_raw
    _write_raw(tmp_path, "spot_klines", {"symbol": "BTCUSDT"}, [[1]], "2026-01-01T00:00:00Z")
    p = next((tmp_path / "data/bronze/binance_cex/spot_klines").glob("*.json"))
    first = p.read_text()
    _write_raw(tmp_path, "spot_klines", {"symbol": "BTCUSDT"}, [[999]], "2026-01-01T00:01:00Z")
    assert p.read_text() == first


def test_phase3_freeze_is_machine_readable_and_separated(tmp_path: Path):
    result = write_phase3_research_outputs(tmp_path)
    assert result["status"] == "BLOCKED_BY_DATA"
    freeze = json.loads((tmp_path / "artifacts/RESEARCH_FREEZE.json").read_text())
    assert freeze["status"] == "DISCOVERY_ONLY_NO_CONFIRMATION"
    assert "R1_PRICE_DISCOVERY" in freeze["hypotheses"]


def test_local_catalog_does_not_mutate_existing(tmp_path: Path):
    from onchain_alpha.data.phase3 import build_local_data_catalog
    p = tmp_path / "existing.parquet"
    pd.DataFrame({"openTime": pd.date_range("2026-01-01", periods=2, tz="UTC"), "BTCUSDT": [1.0, 2.0]}).to_parquet(p, index=False)
    before = p.read_bytes()
    build_local_data_catalog(tmp_path, [tmp_path])
    assert p.read_bytes() == before


def test_event_episode_dedup_uses_cooldown(tmp_path: Path):
    (tmp_path / "artifacts").mkdir(parents=True)
    pd.DataFrame({"event_id": ["a", "b", "c"], "asset_id": ["x", "x", "x"], "event_time": pd.to_datetime(["2026-01-01T00:00Z", "2026-01-01T01:00Z", "2026-01-02T02:00Z"])}).to_parquet(tmp_path / "artifacts/events.parquet", index=False)
    episodes = build_independent_event_episodes(tmp_path, cooldown_hours=24)
    assert episodes.episode_id.nunique() == 2
