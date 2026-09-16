from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd


FACTOR_NAMES = [
    "momentum_1h", "momentum_4h", "momentum_24h", "momentum_7d", "reversal_1h", "realized_vol_24h",
    "volume_momentum", "volume_surprise", "liquidity_mcap", "turnover", "volume_liquidity", "amihud_illiquidity",
    "liquidity_growth", "liquidity_shock", "buy_sell_imbalance", "smart_money_flow_intensity", "smart_money_crowding",
    "signal_count", "signal_breadth", "holder_growth", "holder_acceleration", "holder_concentration", "holder_liquidity_interaction",
    "rank_change", "rank_momentum", "attention_shock", "token_age_days", "audit_score", "chain_volume_breadth", "market_vol_regime",
]


def _num(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    for col in columns:
        if col in frame:
            return pd.to_numeric(frame[col], errors="coerce")
    return pd.Series(np.nan, index=frame.index, dtype=float)


def _exact_lag(values: pd.Series, chain: pd.Series, token: pd.Series, times: pd.Series, hours: int) -> pd.Series:
    """Look up the value at exactly t - hours; never use row position."""
    index = pd.MultiIndex.from_arrays([chain.astype(str), token.astype(str), times])
    lookup = pd.Series(values.to_numpy(), index=index)
    target = pd.MultiIndex.from_arrays([chain.astype(str), token.astype(str), times - timedelta(hours=int(hours))])
    return pd.Series(lookup.reindex(target).to_numpy(dtype=float), index=values.index)


def _time_roll(values: pd.Series, chain: pd.Series, token: pd.Series, times: pd.Series, hours: int, agg: str, min_periods: int = 2) -> pd.Series:
    """Apply a clock-time rolling window within each asset history."""
    result = pd.Series(np.nan, index=values.index, dtype=float)
    groups = pd.DataFrame({"chain": chain.astype(str), "token": token.astype(str)}).groupby(["chain", "token"], sort=False).groups
    for _, positions in groups.items():
        positions = pd.Index(positions)
        part = pd.DataFrame({"time": times.loc[positions], "value": values.loc[positions], "position": positions}).sort_values("time")
        part = part[part["time"].notna()]
        if part.empty:
            continue
        rolled = part.set_index("time")["value"].rolling(f"{int(hours)}h", closed="both", min_periods=min_periods).agg(agg)
        result.loc[part["position"].to_numpy()] = rolled.to_numpy(dtype=float)
    return result


def _residualize_by_timestamp(factor: pd.Series, controls: pd.DataFrame, times: pd.Series) -> pd.Series:
    """Return per-timestamp OLS residuals or NaN when controls are unavailable."""
    result = pd.Series(np.nan, index=factor.index, dtype=float)
    for _, positions in times.groupby(times, sort=False).groups.items():
        positions = pd.Index(positions)
        use = pd.concat([factor.loc[positions].rename("factor"), controls.loc[positions]], axis=1).dropna()
        if len(use) < len(controls.columns) + 2:
            continue
        x = np.column_stack([np.ones(len(use)), use[controls.columns].to_numpy(dtype=float)])
        if np.linalg.matrix_rank(x) < x.shape[1]:
            continue
        beta, *_ = np.linalg.lstsq(x, use["factor"].to_numpy(dtype=float), rcond=None)
        result.loc[use.index] = use["factor"].to_numpy(dtype=float) - x @ beta
    return result


def build_factor_panel(observations: pd.DataFrame) -> pd.DataFrame:
    if observations.empty:
        return pd.DataFrame(columns=["chain", "token_address", "feature_time", *FACTOR_NAMES])
    df = observations.copy()
    df["feature_time"] = pd.to_datetime(df["event_time"].fillna(df["observed_at"]), utc=True, errors="coerce")
    df["token_address"] = df["token_address"].fillna("").astype(str)
    df["chain"] = df["chain"].astype(str)
    df = df.sort_values(["chain", "token_address", "feature_time"]).drop_duplicates(["chain", "token_address", "feature_time"], keep="last").reset_index(drop=True)
    price = _num(df, ["price"]).replace(0, np.nan)
    volume = _num(df, ["volume", "volume_1h", "volume_5m"])
    liquidity = _num(df, ["liquidity"]).replace(0, np.nan)
    mcap = _num(df, ["market_cap"]).replace(0, np.nan)
    holders = _num(df, ["holders"])
    buy, sell = _num(df, ["buy_volume"]), _num(df, ["sell_volume"])
    times = df["feature_time"]
    chain, token = df["chain"], df["token_address"]

    returns_1h = price / _exact_lag(price, chain, token, times, 1) - 1
    returns_4h = price / _exact_lag(price, chain, token, times, 4) - 1
    returns_24h = price / _exact_lag(price, chain, token, times, 24) - 1
    returns_7d = price / _exact_lag(price, chain, token, times, 168) - 1
    vol_24 = _time_roll(returns_1h, chain, token, times, 24, "std")
    vol_mean = _time_roll(volume, chain, token, times, 24, "mean").replace(0, np.nan)
    vol_std = _time_roll(volume, chain, token, times, 24, "std").replace(0, np.nan)
    liquidity_mean = _time_roll(liquidity, chain, token, times, 24, "mean")
    imbalance = (buy - sell) / (buy + sell + 1e-12)
    rank = _num(df, ["rank"])
    smart_flow = _num(df, ["smart_money_flow"])
    smart_hold = _num(df, ["smart_money_holding_percent"])
    top10 = _num(df, ["top10_holding_percent"])
    timestamp_groups = [chain, times]
    liquidity_rank = liquidity.groupby(timestamp_groups, sort=False).rank(pct=True)
    chain_time_volume_breadth = volume.groupby(timestamp_groups, sort=False).transform(lambda s: s.notna().sum())
    market_vol_regime = vol_24.groupby(timestamp_groups, sort=False).transform("mean")

    out = pd.DataFrame({
        "chain": chain.to_numpy(), "token_address": token.to_numpy(), "symbol": df.get("symbol", pd.Series("", index=df.index)).to_numpy(),
        "feature_time": times, "known_at": pd.to_datetime(df["observed_at"], utc=True, errors="coerce"), "is_feature_safe": True,
        "log_market_cap": np.log1p(mcap.to_numpy()), "log_liquidity": np.log1p(liquidity.to_numpy()), "volatility": vol_24.to_numpy(),
        "momentum_1h": returns_1h.to_numpy(), "momentum_4h": returns_4h.to_numpy(), "momentum_24h": returns_24h.to_numpy(), "momentum_7d": returns_7d.to_numpy(),
        "reversal_1h": (-returns_1h).to_numpy(), "realized_vol_24h": vol_24.to_numpy(), "volume_momentum": (volume / _exact_lag(volume, chain, token, times, 24) - 1).to_numpy(),
        "volume_surprise": ((volume - vol_mean) / (vol_std + 1e-12)).to_numpy(), "liquidity_mcap": (liquidity / mcap).to_numpy(),
        "turnover": (volume / mcap).to_numpy(), "volume_liquidity": (volume / liquidity).to_numpy(),
        "amihud_illiquidity": (returns_1h.abs() / (volume + 1e-12)).to_numpy(), "liquidity_growth": (liquidity / _exact_lag(liquidity, chain, token, times, 24) - 1).to_numpy(),
        "liquidity_shock": ((liquidity - liquidity_mean) / (liquidity_mean.abs() + 1e-12)).to_numpy(),
        "buy_sell_imbalance": imbalance.to_numpy(), "smart_money_flow_intensity": (smart_flow / liquidity).to_numpy(), "smart_money_crowding": smart_hold.to_numpy(),
        "signal_count": np.nan, "signal_breadth": np.nan, "holder_growth": (holders / _exact_lag(holders, chain, token, times, 24) - 1).to_numpy(),
        "holder_acceleration": ((holders / _exact_lag(holders, chain, token, times, 1) - 1) - (holders / _exact_lag(holders, chain, token, times, 24) - 1)).to_numpy(), "holder_concentration": top10.to_numpy(),
        "holder_liquidity_interaction": (top10 / (liquidity_rank + 1e-12)).to_numpy(), "rank_change": (1 - rank / _exact_lag(rank, chain, token, times, 1)).to_numpy(),
        "rank_momentum": (1 - rank / _exact_lag(rank, chain, token, times, 24)).to_numpy(), "attention_shock": np.nan, "token_age_days": np.nan,
        "audit_score": _num(df, ["audit_score"]).to_numpy(), "chain_volume_breadth": chain_time_volume_breadth.to_numpy(), "market_vol_regime": market_vol_regime.to_numpy(),
    })
    controls = out[["log_market_cap", "log_liquidity", "volatility"]]
    for factor in FACTOR_NAMES:
        out[f"{factor}_rank"] = out.groupby("feature_time")[factor].rank(pct=True)
        out[f"{factor}_neutralized"] = _residualize_by_timestamp(out[factor], controls, out["feature_time"])
    out["leakage_reason"] = None
    return out
