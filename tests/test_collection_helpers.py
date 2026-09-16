import pandas as pd

from onchain_alpha.backtest import run_backtest
from onchain_alpha.backtest.portfolio import top_bottom_weights
from onchain_alpha.collectors.pagination import iter_pages
from onchain_alpha.collectors.token_collector import _obs_row, deduplicate_tokens
from onchain_alpha.storage import CheckpointStore


def test_checkpoint_roundtrip_and_atomic_write(tmp_path):
    store = CheckpointStore(tmp_path / "checkpoint.json")
    assert store.load() == {}
    store.save({"page": 3, "payload_hashes": ["a"]})
    assert store.load()["page"] == 3


def test_pagination_stops_at_total_page():
    seen = []
    rows = list(iter_pages(lambda page: (seen.append(page) or {"page": {"totalPage": 2}})))
    assert seen == [1, 2] and len(rows) == 2


def test_dedup_and_timestamp_normalization():
    rows = [{"chain": "56", "token_address": "0xA"}, {"chain": "56", "token_address": "0xa"}]
    assert len(deduplicate_tokens(rows)) == 1
    row = _obs_row({"tokenContractAddress": "0x1", "price": "1.0", "time": 1700000000000}, chain="56", source="test", endpoint="x", observed_at="2026-01-01T00:00:00+00:00")
    assert row["event_time"].endswith("+00:00") and row["known_at"] == row["observed_at"]


def test_weights_costs_and_backtest():
    group = pd.DataFrame({"momentum_1h": [1, 2, 3, 4, 5, 6]})
    w = top_bottom_weights(group, "momentum_1h")
    assert abs(w.sum() - 1) < 1e-9
    rows, labels = [], []
    for t in range(30):
        ts = pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=t)
        for i in range(6):
            key = {"chain": "56", "token_address": f"T{i}", "feature_time": ts}
            rows.append({**key, "momentum_1h": i + t / 100})
            labels.append({**key, "forward_return_24h": (i - 2) / 1000, "exit_time_24h": ts + pd.Timedelta(hours=24)})
    result = run_backtest(pd.DataFrame(rows), pd.DataFrame(labels), factor="momentum_1h", horizon=24)
    assert len(result) == 5 and result["cost_bps"].tolist() == [5, 10, 25, 50, 100]
