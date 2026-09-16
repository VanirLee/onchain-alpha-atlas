import pandas as pd

from onchain_alpha.features import build_factor_panel
from onchain_alpha.labels import build_forward_labels


def synthetic_observations():
    rows = []
    for token, base in [("A", 100.0), ("B", 200.0), ("C", 300.0), ("D", 400.0), ("E", 500.0), ("F", 600.0)]:
        for t in range(30):
            rows.append({"chain": "56", "token_address": token, "event_time": f"2026-01-{1 + t // 24:02d}T{t % 24:02d}:00:00+00:00", "observed_at": f"2026-01-{1 + t // 24:02d}T{t % 24:02d}:01:00+00:00", "price": base * (1 + 0.001 * t), "volume": 1000 + t, "liquidity": 100000, "market_cap": base * 1000, "holders": 100 + t, "buy_volume": 600, "sell_volume": 400})
    return pd.DataFrame(rows)


def test_forward_label_is_future_only():
    obs = synthetic_observations()
    labels = build_forward_labels(obs)
    row = labels[(labels.token_address == "A") & (labels.feature_time == "2026-01-01 00:00:00+00:00")].iloc[0]
    assert row["entry_time"] < row["exit_time_1h"]
    assert row["forward_return_1h"] > 0
    assert row["is_feature_safe"] is False or not bool(row["is_feature_safe"])


def test_feature_does_not_use_future_observation():
    obs = synthetic_observations()
    panel = build_factor_panel(obs)
    first = panel[(panel.token_address == "A") & (panel.feature_time == "2026-01-01 00:00:00+00:00")].iloc[0]
    assert pd.isna(first["momentum_1h"])
    assert bool(first["is_feature_safe"])
