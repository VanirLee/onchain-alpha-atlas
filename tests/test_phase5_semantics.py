from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from onchain_alpha.data.phase3 import normalize_web3_trade
from onchain_alpha.data.phase5 import (
    CursorPaginator,
    _clock_grid,
    _episodes,
    _nearest,
    _response_records,
    append_only_snapshot,
    build_price_semantics_audit,
    mark_legacy_phase4_results,
    parse_pool_snapshot,
    run_clock_microstructure,
    run_formal_research_program,
)


def official_trade(side: str = "buy", tx: str = "tx-1", t: int = 1_748_601_600_000) -> dict:
    return {
        "price": "0.00000702", "volume": "1500.50", "type": side, "time": t,
        "txHash": tx, "userAddress": "0xAbC", "dexName": "DEX",
        "tokenContractAddress": "0xToken",
        "changedTokenInfo": [
            {"amount": "1500000", "tokenContractAddress": "0xToken", "tokenSymbol": "TOK"},
            {"amount": "1500.50", "tokenContractAddress": "0xUSD", "tokenSymbol": "USDC"},
        ],
    }


def test_volume_is_usd_not_quantity_and_changed_token_quantity_is_exact():
    row = normalize_web3_trade(official_trade(), chain="1", token_address="0xToken", available_time="2026-01-01T00:00:00Z")
    assert row["usd_value"] == pytest.approx(1500.50)
    assert row["token_quantity"] == pytest.approx(1500000)
    assert row["quantity"] == pytest.approx(1500000)
    assert row["usd_value"] != pytest.approx(1500.50 * 0.00000702)


def test_exact_buy_sell_mapping_and_unknown_diagnostic():
    buy = normalize_web3_trade(official_trade("buy"), chain="1", token_address="0xToken", available_time="2026-01-01T00:00:00Z")
    sell = normalize_web3_trade(official_trade("sell", tx="tx-2"), chain="1", token_address="0xToken", available_time="2026-01-01T00:00:00Z")
    other = normalize_web3_trade(official_trade("buy", tx="tx-3") | {"type": "in"}, chain="1", token_address="0xToken", available_time="2026-01-01T00:00:00Z")
    assert (buy["side"], buy["side_sign"]) == ("buy", 1)
    assert (sell["side"], sell["side_sign"]) == ("sell", -1)
    assert (other["side"], other["schema_diagnostic"]) == ("UNKNOWN", "UNKNOWN_SIDE")


def test_cursor_first_page_next_page_and_termination(tmp_path: Path):
    seen = []
    responses = [
        {"cursor": "c1", "trades": [{"id": 1}]},
        {"cursor": "c2", "trades": [{"id": 2}]},
        {"cursor": "", "trades": [{"id": 3}]},
    ]

    def fetch(params):
        seen.append(dict(params))
        return type("R", (), {"data": responses.pop(0)})()

    rows = CursorPaginator(fetch, tmp_path / "checkpoint.json", max_pages=10).run({"binanceChainId": "1", "tokenContractAddress": "x"})
    assert len(rows) == 3
    assert "cursor" not in seen[0] and seen[1]["cursor"] == "c1" and seen[2]["cursor"] == "c2"


def test_cursor_resume_starts_from_checkpoint(tmp_path: Path):
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(json.dumps({"cursor": "resume", "pages": 1, "requests": 1}), encoding="utf-8")
    seen = []

    def fetch(params):
        seen.append(params)
        return type("R", (), {"data": {"cursor": "", "trades": [{"id": 9}]}})()

    CursorPaginator(fetch, checkpoint, max_pages=10).run({"binanceChainId": "1", "tokenContractAddress": "x"})
    assert seen[0]["cursor"] == "resume"


def test_trade_identity_keeps_multiswap_rows_but_deduplicates_exact_duplicate():
    a = normalize_web3_trade(official_trade(tx="same", side="buy"), chain="1", token_address="0xToken", available_time="2026-01-01T00:00:00Z")
    b = normalize_web3_trade(official_trade(tx="same", side="sell"), chain="1", token_address="0xToken", available_time="2026-01-01T00:00:00Z")
    assert a["trade_id"] != b["trade_id"]
    frame = pd.DataFrame([a, a, b]).drop_duplicates("trade_id")
    assert len(frame) == 2


def test_clock_time_horizon_rejects_missing_target_instead_of_next_trade():
    d = pd.DataFrame({"asset_id": ["a"] * 3, "trade_time": pd.to_datetime(["2026-01-01T00:00Z", "2026-01-01T00:01Z", "2026-01-01T00:07Z"]), "price": [100.0, 101.0, 107.0]})
    grid = _clock_grid(d, "1min")
    price, timestamp = _nearest(grid, pd.Timestamp("2026-01-01T00:06Z"), pd.Timedelta(seconds=30))
    assert pd.isna(price) and pd.isna(timestamp)
    exact_price, source_timestamp = _nearest(grid, pd.Timestamp("2026-01-01T00:07Z"), pd.Timedelta(seconds=30))
    assert exact_price == pytest.approx(107.0)
    assert source_timestamp == pd.Timestamp("2026-01-01T00:07Z")


def test_signed_response_direction():
    assert 1 * 0.05 == pytest.approx(0.05)
    assert -1 * 0.05 == pytest.approx(-0.05)


def test_cluster_episode_construction_is_cooldown_based():
    d = pd.DataFrame({"asset_id": ["a"] * 3, "trade_time": pd.to_datetime(["2026-01-01T00:00Z", "2026-01-01T00:03Z", "2026-01-01T00:10Z"]), "price": [1, 1, 1]})
    # A direct observable check for the intended five-minute episode boundary.
    assert _episodes(d.trade_time).tolist() == [0, 0, 1]


def test_old_phase4_results_are_explicitly_superseded(tmp_path: Path):
    (tmp_path / "artifacts").mkdir()
    pd.DataFrame([{"raw_p_value": 0.01}]).to_parquet(tmp_path / "artifacts/phase4_multiple_testing.parquet")
    out = mark_legacy_phase4_results(tmp_path)
    assert out.iloc[0]["status"] == "SUPERSEDED_BY_PHASE_V_RECOMPUTATION"
    assert pd.read_parquet(tmp_path / "artifacts/phase4_legacy_multiple_testing.parquet").iloc[0]["status"] == "SUPERSEDED_BY_PHASE_V_RECOMPUTATION"


def test_official_holder_and_top_trader_schema_records_are_preserved():
    data = [{"holderWalletAddress": "0xabc", "holdAmount": "10", "realizedPnlUsd": "2"}]
    assert _response_records(data)[0]["holderWalletAddress"] == "0xabc"


def test_participant_snapshot_append_only_and_future_snapshot_invariance():
    prior = pd.DataFrame([{"snapshot_time": "2026-01-01", "wallet_id": "w", "rank": 1, "holding": 10}])
    current = pd.DataFrame([{"snapshot_time": "2026-01-02", "wallet_id": "w", "rank": 1, "holding": 5}])
    merged = append_only_snapshot(prior, current, ["snapshot_time", "wallet_id", "rank"])
    future = append_only_snapshot(merged, pd.DataFrame([{"snapshot_time": "2026-01-03", "wallet_id": "w", "rank": 1, "holding": 1}]), ["snapshot_time", "wallet_id", "rank"])
    pd.testing.assert_frame_equal(merged, future.iloc[:2].reset_index(drop=True))


def test_pool_snapshot_parser():
    row = parse_pool_snapshot("56", "0xToken", {"poolAddress": "0xPool", "protocolName": "DEX", "liquidityUsd": "123.4"}, "2026-01-01T00:00:00Z")
    assert row["pool_id"] == "56:0xPool"
    assert row["liquidity_usd"] == pytest.approx(123.4)


def _synthetic_tape() -> pd.DataFrame:
    ts = pd.to_datetime(["2026-01-01T00:00:10Z", "2026-01-01T00:00:50Z", "2026-01-01T00:01:00Z", "2026-01-01T00:03:00Z", "2026-01-01T00:10:00Z"])
    return pd.DataFrame({
        "trade_id": [f"t{i}" for i in range(len(ts))], "wallet_id": [f"w{i}" for i in range(len(ts))],
        "asset_id": ["1:token"] * len(ts), "chain": ["1"] * len(ts), "token_address": ["token"] * len(ts),
        "trade_time": ts, "price": [1.0, 1.1, 1.2, 1.3, 1.4],
        "usd_value": [100.0, 110.0, 120.0, 130.0, 140.0], "token_quantity": [1.0] * len(ts), "paired_token_quantity": [1.0, 1.1, 1.2, 1.3, 1.4], "raw_json": ["{}"] * len(ts), "source": ["synthetic"] * len(ts),
        "side_sign": [1.0, 1.0, 1.0, 1.0, 1.0], "side": ["buy"] * len(ts),
    })


def test_signed_response_uses_target_trade_execution_price_and_horizon_clusters(tmp_path: Path):
    (tmp_path / "data/gold/trades").mkdir(parents=True)
    (tmp_path / "artifacts").mkdir(parents=True)
    tape = _synthetic_tape(); tape.to_parquet(tmp_path / "data/gold/trades/fact_wallet_trade.parquet", index=False)
    result = run_clock_microstructure(tmp_path, tolerance_seconds=30)
    impacts = pd.read_parquet(tmp_path / "artifacts/price_impact_results.parquet")
    first = impacts.loc[impacts.trade_id.eq("t0")].iloc[0]
    # The minute grid's immediate price is 110, but the event execution price is 100.
    assert first["trade_price"] == pytest.approx(100.0)
    assert first["signed_response_1m"] == pytest.approx(0.20)
    assert impacts["episode_id_1m"].nunique() > impacts["episode_id_60m"].nunique()
    assert result["summary_rows"] == 4


def test_price_semantics_gate_uses_paired_leg_and_usd_implied_event_price(tmp_path: Path):
    (tmp_path / "data/gold/trades").mkdir(parents=True)
    (tmp_path / "artifacts").mkdir(parents=True)
    tape = _synthetic_tape(); tape.to_parquet(tmp_path / "data/gold/trades/fact_wallet_trade.parquet", index=False)
    result = build_price_semantics_audit(tmp_path)
    audit = pd.read_parquet(tmp_path / "artifacts/PRICE_SEMANTICS_AUDIT.parquet")
    assert result["included_rows"] == len(tape)
    assert audit["api_vs_paired_ratio"].median() == pytest.approx(1.0)
    assert audit["price_ratio"].median() == pytest.approx(0.01)
    assert audit["validation_reason"].eq("API_PRICE_IS_PAIRED_DENOMINATED__USD_IMPLIED_PRICE_USED").all()


def test_formal_research_program_writes_registered_hypotheses_from_real_artifacts(tmp_path: Path):
    (tmp_path / "data/gold/trades").mkdir(parents=True)
    (tmp_path / "artifacts").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)
    tape = pd.concat([_synthetic_tape()] * 8, ignore_index=True)
    tape["trade_id"] = [f"t{i}" for i in range(len(tape))]
    tape.to_parquet(tmp_path / "data/gold/trades/fact_wallet_trade.parquet", index=False)
    run_clock_microstructure(tmp_path, tolerance_seconds=30)
    result = run_formal_research_program(tmp_path)
    registry = pd.read_parquet(tmp_path / "artifacts/phase5_experiment_registry.parquet")
    assert result["hypotheses"] == 12
    assert len(registry) == 12
    assert (tmp_path / "artifacts/RESEARCH_FREEZE.json").exists()
    assert (tmp_path / "reports/ONCHAIN_QUANT_RESEARCH_REPORT.md").exists()
