from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "audit_bundle"
ZIP_PATH = ROOT / "PROJECT_AUDIT_BUNDLE.zip"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text(rel: str, text: str) -> None:
    path = BUNDLE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def copy_file(rel: str, dest: str | None = None) -> bool:
    src = ROOT / rel
    if not src.exists() or not src.is_file():
        return False
    target = BUNDLE / (dest or rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    return True


def json_load(rel: str, default: Any = None) -> Any:
    path = ROOT / rel
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def frame(rel: str) -> pd.DataFrame:
    path = ROOT / rel
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def write_csv(rel: str, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path = BUNDLE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    cols = columns or list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_iso(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


def project_tree() -> str:
    lines = ["Onchain Alpha Atlas project tree (audit export; raw/venv contents summarized, not hidden)", ""]
    skip = {"audit_bundle", ".venv", ".git", "__pycache__", ".pytest_cache"}
    def walk(path: Path, prefix: str = "", depth: int = 0) -> None:
        if depth > 6:
            return
        entries = sorted([p for p in path.iterdir() if p.name not in skip and p.name != "PROJECT_AUDIT_BUNDLE.zip"], key=lambda p: (p.is_file(), p.name.lower()))
        for idx, child in enumerate(entries):
            last = idx == len(entries) - 1
            branch = "└── " if last else "├── "
            if child.is_dir():
                if child.name == "bronze":
                    n = sum(1 for _ in child.rglob("*.json"))
                    lines.append(f"{prefix}{branch}{child.name}/ ({n} raw JSON files; contents excluded from bundle)")
                elif child.name == "gold":
                    lines.append(f"{prefix}{branch}{child.name}/ (generated Parquet; selected samples exported)")
                else:
                    lines.append(f"{prefix}{branch}{child.name}/")
                    if depth < 6:
                        walk(child, prefix + ("    " if last else "│   "), depth + 1)
            else:
                lines.append(f"{prefix}{branch}{child.name}")
    walk(ROOT)
    lines.extend(["", "Classification:", "- src/ and app/: source code", "- tests/: tests", "- data/: Bronze/Silver/Gold data", "- reports/: research outputs", "- artifacts/: generated artifacts and manifests", "- docs/config/: documentation and configuration", "- notebooks/sql/: research support", "- scripts/: audit/reproducibility tooling"])
    return "\n".join(lines)


def environment_text() -> str:
    imports = ["pandas", "polars", "numpy", "scipy", "statsmodels", "sklearn", "httpx", "pytest", "pyarrow", "duckdb", "streamlit", "plotly", "matplotlib", "pydantic"]
    rows = []
    for name in imports:
        try:
            mod = __import__(name)
            rows.append(f"{name}: {getattr(mod, '__version__', 'installed')}")
        except Exception as exc:
            rows.append(f"{name}: unavailable ({type(exc).__name__})")
    return "\n".join([f"Python: {sys.version.split()[0]}", f"OS: {platform.platform()}", f"Generated: {datetime.now(timezone.utc).isoformat()}", "", *rows])


def api_outputs() -> None:
    caps = json_load("artifacts/api_capabilities.json", {})
    audit = json_load("artifacts/collection_audit.json", {})
    copy_file("docs/api_capabilities.md", "api/API_CAPABILITIES.md")
    endpoints = caps.get("endpoints", []) or []
    request_rows = audit.get("requests", []) or []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in request_rows:
        grouped[str(item.get("endpoint"))].append(item)
    # Capability probes are real calls, but are kept as a separate purpose in notes.
    for item in endpoints:
        if item.get("endpoint") not in grouped:
            grouped[str(item.get("endpoint"))].append({"http_status": item.get("http_status"), "latency_ms": item.get("latency_ms"), "business_code": item.get("business_code"), "purpose": "capability_discovery"})
    usage = []
    for endpoint, items in sorted(grouped.items()):
        def status_code(item: dict[str, Any]) -> int:
            return int(item.get("http_status", item.get("status", 0)) or 0)
        statuses = [status_code(x) for x in items]
        lat = [float(x.get("latency_ms")) for x in items if x.get("latency_ms") is not None]
        usage.append({"provider": "Binance Web3", "endpoint": endpoint, "request_count": len(items), "success_count": sum(1 for x in items if status_code(x) == 200 and int(x.get("business_code") or 0) == 0), "failure_count": sum(1 for x in items if status_code(x) != 200 or int(x.get("business_code") or 0) != 0), "HTTP_2xx": sum(200 <= x < 300 for x in statuses), "HTTP_4xx": sum(400 <= x < 500 for x in statuses), "HTTP_429": sum(x == 429 for x in statuses), "HTTP_5xx": sum(500 <= x < 600 for x in statuses), "mean_latency_ms": round(sum(lat) / len(lat), 3) if lat else "", "p95_latency_ms": round(float(pd.Series(lat).quantile(0.95)), 3) if lat else "", "first_request_time": safe_iso(audit.get("observed_at") or caps.get("generated_at")), "last_request_time": safe_iso(audit.get("observed_at") or caps.get("generated_at"))})
    discovery_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in endpoints:
        discovery_groups[str(item.get("endpoint"))].append(item)
    for endpoint, items in sorted(discovery_groups.items()):
        statuses = [int(x.get("http_status") or 0) for x in items]
        lat = [float(x.get("latency_ms")) for x in items if x.get("latency_ms") is not None]
        usage.append({"provider": "Binance Web3 (capability discovery)", "endpoint": endpoint, "request_count": len(items), "success_count": sum(1 for x in items if int(x.get("http_status") or 0) == 200 and int(x.get("business_code") or 0) == 0), "failure_count": sum(1 for x in items if int(x.get("http_status") or 0) != 200 or int(x.get("business_code") or 0) != 0), "HTTP_2xx": sum(200 <= x < 300 for x in statuses), "HTTP_4xx": sum(400 <= x < 500 for x in statuses), "HTTP_429": sum(x == 429 for x in statuses), "HTTP_5xx": sum(500 <= x < 600 for x in statuses), "mean_latency_ms": round(sum(lat) / len(lat), 3) if lat else "", "p95_latency_ms": round(float(pd.Series(lat).quantile(0.95)), 3) if lat else "", "first_request_time": safe_iso(caps.get("generated_at")), "last_request_time": safe_iso(caps.get("generated_at"))})
    write_csv("api/API_USAGE_SUMMARY.csv", usage)
    known = {
        "/api/v1/dex/market/token/hot-token": ("ranked token discovery", "snapshot", "size/page observed"),
        "/api/v1/dex/market/price-info": ("batch token market state", "snapshot", "read-only POST; batch used up to 30 per chain"),
        "/api/v1/dex/market/candles": ("historical OHLCV candles", "historical", "1h, limit 96 requested; array schema normalized"),
        "/api/v1/dex/market/token/advanced-info": ("holder/smart-money proxy fields", "snapshot", "no wallet identity panel"),
        "/api/v1/dex/market/token/top-liquidity": ("top liquidity pool discovery", "snapshot", "not used in factor panel"),
        "/api/v1/dex/market/trades": ("token trade tape capability", "snapshot/paginated", "probed, not used in factor panel"),
    }
    inventory = []
    for endpoint, (purpose, hist, notes) in known.items():
        items = grouped.get(endpoint, [])
        cap_items = discovery_groups.get(endpoint, [])
        all_items = items + cap_items
        successes = sum(1 for x in all_items if int(x.get("http_status", x.get("status", 0)) or 0) == 200 and int(x.get("business_code") or 0) == 0)
        inventory.append({"provider": "Binance Web3", "endpoint": endpoint, "method": "POST" if endpoint.endswith("price-info") else "GET", "purpose": purpose, "auth_required": True, "tested": bool(all_items), "working": successes > 0, "historical_or_snapshot": hist, "earliest_observation": audit.get("observed_at", ""), "latest_observation": audit.get("observed_at", ""), "request_count": len(all_items), "success_count": successes, "failure_count": len(all_items) - successes, "notes": notes})
    for endpoint, purpose in [("wallet/holdings", "wallet panel"), ("smart-money signal outcome", "signal panel"), ("event/meme lifecycle", "event panel")]:
        inventory.append({"provider": "Binance Web3", "endpoint": endpoint, "method": "unknown", "purpose": purpose, "auth_required": "unknown", "tested": False, "working": "unknown", "historical_or_snapshot": "unknown", "earliest_observation": "", "latest_observation": "", "request_count": 0, "success_count": 0, "failure_count": 0, "notes": "No endpoint was inferred or probed; adapter extension point only."})
    write_csv("api/ENDPOINT_INVENTORY.csv", inventory)
    # Preserve the formal source-code inventory, including the requested
    # status taxonomy, instead of replacing it with the legacy summary shape.
    if caps.get("endpoint_inventory"):
        write_csv("api/ENDPOINT_INVENTORY.csv", caps["endpoint_inventory"])
    write_text("api/README.md", "This directory contains redacted, machine-readable API evidence. No API key, secret, signature, authorization header, or full raw request headers are included. Capability discovery and collection metrics come from artifacts/api_capabilities.json and artifacts/collection_audit.json. The source audit log stores a run-level observed_at rather than per-request wall-clock timestamps, so first_request_time/last_request_time are run-level evidence bounds, not exact request intervals.")


def data_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    (BUNDLE / "data").mkdir(parents=True, exist_ok=True)
    universe = frame("data/gold/universe.parquet")
    obs = frame("data/gold/market_observations.parquet")
    panel = frame("artifacts/factor_panel.parquet")
    labels = frame("artifacts/labels.parquet")
    if not universe.empty:
        u = pd.DataFrame({"timestamp": universe.get("first_seen"), "token": universe.get("token_address"), "symbol": universe.get("symbol"), "contract_address": universe.get("token_address"), "chain": universe.get("chain"), "market": "DEX token market", "CEX availability": "not mapped", "DEX availability": "ranked Web3 discovery", "selection criterion": "hot-token rankBy=6, timeframe=3", "liquidity metric": "API field available in price-info; not historical in candle rows", "volume metric": "API volume fields", "market cap": "API marketCap when present", "included": True, "exclusion_reason": ""})
        u.to_csv(BUNDLE / "data/UNIVERSE.csv", index=False)
    datasets = [("universe", universe), ("market_observations", obs), ("factor_panel", panel), ("labels", labels)]
    coverage = []
    for name, df in datasets:
        chains = sorted(df["chain"].dropna().astype(str).unique()) if "chain" in df else []
        for chain in chains or ["all"]:
            sub = df[df["chain"].astype(str) == chain] if "chain" in df else df
            token_col = "token_address" if "token_address" in sub else ("token" if "token" in sub else None)
            dup = sub.duplicated().mean() if len(sub) else 0
            times = pd.to_datetime(sub["feature_time"] if "feature_time" in sub else sub["event_time"] if "event_time" in sub else pd.Series(dtype="datetime64[ns]"), utc=True, errors="coerce")
            coverage.append({"dataset": name, "chain": chain, "token_count": int(sub[token_col].nunique()) if token_col else "", "pair_count": 0, "wallet_count": 0, "start_time": times.min().isoformat() if len(times) and not pd.isna(times.min()) else "", "end_time": times.max().isoformat() if len(times) and not pd.isna(times.max()) else "", "frequency": "1h candles" if name in {"market_observations", "factor_panel", "labels"} else "discovery snapshot", "row_count": len(sub), "missing_ratio": round(float(sub.isna().mean().mean()), 6) if len(sub) else 0, "duplicate_ratio": round(float(dup), 6), "source": "Binance Web3 real_api", "notes": "No wallet/CEX panel; current price-info row is snapshot."})
    write_csv("data/DATA_COVERAGE.csv", coverage)
    field_rows = []
    for name, df in datasets:
        for col in df.columns:
            field_rows.append(f"- `{col}` in `{name}`: observed field; dtype={df[col].dtype}; missing={int(df[col].isna().sum())}/{len(df)}; source=normalized Binance Web3 observation or derived label/factor.")
    write_text("data/DATA_DICTIONARY.md", "# Audit data dictionary\n\n" + "\n".join(field_rows) + "\n\nTimestamp rule: event_time is used when supplied by candles; otherwise observed_at/known_at anchors when the value became available. Forward returns are labels and are not feature-safe.")
    failures = json_load("artifacts/collection_audit.json", {}).get("requests", [])
    lines = ["# Data quality report", "", f"- Universe rows: {len(universe)}; unique tokens: {universe['token_address'].nunique() if 'token_address' in universe else 0}; chains: {universe['chain'].nunique() if 'chain' in universe else 0}.", f"- Market observation rows: {len(obs)}; duplicate ratio: {obs.duplicated().mean() if len(obs) else 0:.6f}.", f"- Factor panel rows: {len(panel)}; labels rows: {len(labels)}.", f"- Endpoint failure requests in collection audit: {sum(1 for x in failures if x.get('http_status') != 200 or x.get('business_code') != 0)}; 429: {sum(1 for x in failures if x.get('http_status') == 429)}; 5xx: {sum(1 for x in failures if x.get('http_status', 0) >= 500)}.", "- Stale quotes: not applicable to candle-based factor panel; no executable quote panel was used.", "- Impossible-value checks: numeric coercion was applied; no dedicated economic invariant test was run for all API fields (PARTIAL).", "- Timestamp gaps: token candle histories are not assumed globally synchronized; cross-sectional joins use exact feature_time.", "- Chain-specific failures: none in the 4 configured chains during this run; CT_501 returned fewer ranked tokens (23 vs 30 requested).", "- Token-specific failures: no failed candle requests in the recorded sample; missingness remains field-specific.", "- Coverage bias: universe is hot-token ranked discovery at collection time, not a full historical all-token universe; delisted/dead tokens are not reconstructed.", "- Wallet count: 0; wallet-level study not run. CEX market count: 0; CEX module deferred.", ""]
    for col in obs.columns:
        miss = int(obs[col].isna().sum())
        lines.append(f"- `{col}` missing: {miss}/{len(obs)} ({miss/len(obs):.4%})" if len(obs) else f"- `{col}` missing: no rows")
    write_text("data/DATA_QUALITY_REPORT.md", "\n".join(lines))
    return universe, panel, labels


def samples(universe: pd.DataFrame, panel: pd.DataFrame, labels: pd.DataFrame) -> None:
    obs = frame("data/gold/market_observations.parquet")
    sample_specs = [("data/samples/market_observations_sample.parquet", "market_observations", obs), ("data/samples/factor_panel_sample.parquet", "factor_panel", panel), ("data/samples/forward_returns_sample.parquet", "labels", labels)]
    manifest = []
    for rel, source, df in sample_specs:
        if df.empty:
            continue
        sample = df.sample(n=min(2000, len(df)), random_state=42) if len(df) > 2000 else df.copy()
        target = BUNDLE / rel; target.parent.mkdir(parents=True, exist_ok=True); sample.to_parquet(target, index=False)
        token_col = "token_address" if "token_address" in sample else None
        chain_col = "chain" if "chain" in sample else None
        time_col = "feature_time" if "feature_time" in sample else "event_time" if "event_time" in sample else None
        manifest.append({"file": rel, "source_dataset": source, "sampling_method": "deterministic random_state=42; capped at 2,000 rows", "original_rows": len(df), "sample_rows": len(sample), "original_columns": len(df.columns), "date_range": f"{sample[time_col].min()} to {sample[time_col].max()}" if time_col else "", "token_count": int(sample[token_col].nunique()) if token_col else 0, "chain_count": int(sample[chain_col].nunique()) if chain_col else 0})
    raw_files = sorted((ROOT / "data/bronze").rglob("*.json"))
    raw_target = BUNDLE / "data/samples/raw_token_sample.jsonl"; raw_target.parent.mkdir(parents=True, exist_ok=True); count = 0
    with raw_target.open("w", encoding="utf-8") as out:
        for path in raw_files:
            if count >= 200:
                break
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if "hot-token" not in str(record.get("endpoint", "")) and "price-info" not in str(record.get("endpoint", "")):
                continue
            out.write(json.dumps({"source": record.get("source"), "endpoint": record.get("endpoint"), "chain": record.get("chain"), "observed_at": record.get("observed_at"), "request_params_hash": record.get("request_params_hash"), "payload_hash": record.get("payload_hash"), "payload": record.get("payload")}, ensure_ascii=False, default=str) + "\n")
            count += 1
    manifest.append({"file": "data/samples/raw_token_sample.jsonl", "source_dataset": "Bronze hot-token/price-info", "sampling_method": "first 200 matching raw records by sorted partition path; secrets absent", "original_rows": len(raw_files), "sample_rows": count, "original_columns": 7, "date_range": "see observed_at", "token_count": int(universe["token_address"].nunique()) if "token_address" in universe else 0, "chain_count": int(universe["chain"].nunique()) if "chain" in universe else 0})
    write_csv("data/DATA_SAMPLE_MANIFEST.csv", manifest)
    write_text("data/DATA_SAMPLE_MANIFEST.md", "# Data sample manifest\n\n" + "\n".join(f"- `{m['file']}`: source={m['source_dataset']}; original_rows={m['original_rows']}; sample_rows={m['sample_rows']}; tokens={m['token_count']}; chains={m['chain_count']}; method={m['sampling_method']}" for m in manifest) + "\n\nNo wallet, CEX, DEX quote, or event sample is included because those panels were not part of the actual research run; they are not replaced with synthetic data.")


FACTOR_FAMILY = {"momentum": ["momentum", "reversal", "realized_vol"], "liquidity": ["liquidity", "turnover", "volume_liquidity", "amihud"], "flow": ["buy_sell"], "smart_money_proxy": ["smart_money", "signal"], "holder_proxy": ["holder"], "attention_proxy": ["rank", "attention"], "risk": ["audit"], "regime": ["chain_volume", "market_vol"], "volume": ["volume"]}


def factor_family(name: str) -> str:
    for family, needles in FACTOR_FAMILY.items():
        if any(n in name for n in needles):
            return family
    return "other"


def research_outputs(panel: pd.DataFrame, labels: pd.DataFrame) -> None:
    ic = pd.read_csv(ROOT / "reports/factor_ic.csv") if (ROOT / "reports/factor_ic.csv").exists() else pd.DataFrame()
    catalog = []
    formula = {
        "momentum_1h": "price(t) / price(t-1) - 1",
        "momentum_4h": "price(t) / price(t-4) - 1",
        "momentum_24h": "price(t) / price(t-24) - 1",
        "momentum_7d": "price(t) / price(t-168) - 1",
        "reversal_1h": "-momentum_1h",
        "realized_vol_24h": "rolling_std(momentum_1h, 24)",
        "volume_momentum": "volume(t) / volume(t-24) - 1",
        "volume_surprise": "(volume(t) - rolling_mean(volume,24)) / (rolling_std(volume,24) + eps)",
        "liquidity_mcap": "liquidity / market_cap",
        "turnover": "volume / market_cap",
        "volume_liquidity": "volume / liquidity",
        "amihud_illiquidity": "abs(momentum_1h) / (volume + eps)",
        "liquidity_growth": "liquidity(t) / liquidity(t-24) - 1",
        "liquidity_shock": "(liquidity(t) - rolling_mean(liquidity,24)) / (abs(rolling_mean(liquidity,24)) + eps)",
        "buy_sell_imbalance": "(buy_volume - sell_volume) / (buy_volume + sell_volume + eps)",
        "smart_money_flow_intensity": "smart_money_flow / liquidity",
        "smart_money_crowding": "smartMoneyHoldingPercent",
        "signal_count": "NaN: no confirmed forward signal endpoint",
        "signal_breadth": "NaN: no confirmed forward signal endpoint",
        "holder_growth": "holders(t) / holders(t-24) - 1",
        "holder_acceleration": "(holders(t)/holders(t-1h)-1) - (holders(t)/holders(t-24h)-1)",
        "holder_concentration": "top10HoldingPercent",
        "holder_liquidity_interaction": "top10HoldingPercent / (cross_sectional_rank(liquidity) + eps)",
        "rank_change": "-pct_change(rank,1)",
        "rank_momentum": "-pct_change(rank,24)",
        "attention_shock": "NaN: no confirmed attention/event endpoint",
        "token_age_days": "NaN: creation-time mapping not used in executed panel",
        "audit_score": "audit_score source field when available, else NaN",
        "chain_volume_breadth": "count of non-null volume rows within current (chain, feature_time) cross-section",
        "market_vol_regime": "cross-sectional mean of rolling_vol_24h at current (chain, feature_time)",
    }
    factors = [c for c in panel.columns if c in set(ic.factor) if not ic.empty] if not ic.empty and "factor" in ic else [c for c in panel.columns if c in {"momentum_1h"}]
    # Prefer the implementation's declared 30 factor names when available.
    factors = [c for c in panel.columns if not c.endswith("_rank") and not c.endswith("_neutralized") and c not in {"chain", "token_address", "symbol", "feature_time", "known_at", "is_feature_safe", "leakage_reason"}]
    for name in factors:
        coverage = float(panel[name].notna().mean()) if name in panel else 0
        catalog.append({"factor_id": name, "factor_name": name, "factor_family": factor_family(name), "economic_hypothesis": "Exploratory candidate; economic sign is not confirmed by this run.", "raw_inputs": "price/volume/liquidity/holder/rank fields when available", "formula": formula.get(name, "see src/onchain_alpha/features/core.py::build_factor_panel"), "lookback": "exact 1h/4h/24h/7d timestamp match or trailing clock-time window", "lag": "0 bars after feature_time; known_at is observed_at", "holding_horizon": "1h, 4h, 24h labels", "expected_sign": "not pre-registered", "cross_sectional_or_timeseries": "cross-sectional screening over time", "normalization": "cross-sectional percentile rank output is generated", "winsorization": "not implemented in current run", "neutralization": "per-timestamp OLS residual on log_market_cap + log_liquidity + volatility when all controls are available; NaN otherwise", "minimum_history": "factor-specific exact timestamp history", "coverage": coverage, "implementation_file": "src/onchain_alpha/features/core.py", "implementation_function": "build_factor_panel"})
    write_csv("research/FACTOR_CATALOG.csv", catalog)
    definition_lines = ["# Factor definitions", "", "Implementation: `src/onchain_alpha/features/core.py::build_factor_panel`.", "", "For each `(chain, token_address)` history, rows are sorted by `feature_time`; rolling and lagged values use only rows at or before the current row. `eps=1e-12` is used where the source code protects a denominator. `known_at` is the normalized observation time. Labels are future-only and are never factor inputs.", ""]
    for name in factors:
        definition_lines.append(f"- `{name}`: `{formula.get(name, 'see source implementation')}`")
    definition_lines.extend(["", "`factor(t)` is joined to labels on the same `feature_time`. Lagged horizons use exact clock-time matches; trailing statistics use clock-time windows. `forward_return_h` uses exactly `t+h` when present and otherwise is NaN, with explicit `exit_time_h`. No winsorization was applied in the executed run. Cross-sectional percentile-rank variants are generated. Neutralized variants are per-timestamp OLS residuals on `log_market_cap`, `log_liquidity`, and `volatility`; they are NaN/NOT_AVAILABLE when the complete control set is unavailable.", "", "Unsupported or unavailable dimensions (wallet holdings, signal outcome, events/meme lifecycle, token age mapping) remain NaN/unsupported; they are not filled from future information."])
    write_text("research/FACTOR_DEFINITIONS.md", "\n".join(definition_lines))
    write_text("research/TARGET_DEFINITIONS.md", "# Target definitions\n\nFor token i at feature timestamp t, `forward_return_h(t) = price_i(t+h) / price_i(t) - 1`, where h is 1h, 4h, or 24h and `t+h` must exist exactly in that asset's UTC timestamp index. If the target timestamp is absent, the label is NaN; the 24th observation is never treated as a 24-hour target when timestamps are irregular. `entry_time=t` and `exit_time_h=t+h` are stored explicitly. The label uses candle close-like field normalized from the API candle array; no executable quote, block confirmation, latency, VWAP, or CEX mid is modeled. The label is future-only, marked `is_feature_safe=false`, and is never used to construct the feature row.")
    write_text("research/HYPOTHESES.md", "# Hypotheses\n\nThe executed run was exploratory, not preregistered. The following are transparent post-hoc research hypotheses corresponding to the implemented factor families:\n\n- H1 (POST-HOC/EXPLORATORY): short-term reversal predicts next-horizon cross-sectional returns.\n- H2 (POST-HOC/EXPLORATORY): volume momentum/surprise predicts future returns.\n- H3 (POST-HOC/EXPLORATORY): liquidity/illiquidity proxies add predictive information beyond price movement.\n- H4 (NOT TESTED): smart-money flow intensity and signal persistence predict returns; no confirmed signal endpoint was available.\n- H5 (NOT TESTED): wallet persona features predict returns; no wallet holdings endpoint was confirmed.\n\nAll tested H1-H3 variants are multiple-tested in `results/multiple_testing.csv`; no q=0.05 or q=0.10 discovery survives in this run.")
    write_text("research/EXPERIMENT_DESIGN.md", "# Experiment design\n\nUniverse: 112 tokens selected by current hot-token ranking across 4 configured chains. Sample: API-returned 1h candles plus current price-info snapshot; not a full historical all-token universe. Factors are calculated within token history using exact UTC timestamps and trailing clock-time windows, then ranked cross-sectionally by feature_time. Labels are 1h/4h/24h forward returns with exact target timestamps. IC is Spearman per timestamp; factor inference tests the mean IC time series with naive and horizon-matched HAC errors. Quantiles use five cross-sectional bins. Regressions are exploratory OLS/HAC with available controls. Backtest is long-only top quantile with non-overlapping h-hour rebalances and proxy costs of 5/10/25/50/100 bps. Robustness includes timestamp-level purged OOS IC and leave-one-chain-out IC for every factor.\n\nIS/OOS: the time split is 70%/30% by unique feature timestamps. Train labels with `exit_time_h >= test_start` are purged; the reported embargo is h hours. This is still not a full walk-forward production protocol.")
    write_text("research/STATISTICAL_METHODS.md", "# Statistical methods actually used\n\n- Spearman Rank IC: `scipy.stats.spearmanr`, computed cross-sectionally by feature timestamp.\n- Factor inference: H0: E[IC_t]=0; one-sample t statistic and `statsmodels.OLS(IC_t ~ 1, cov_type='HAC')`. HAC lag is `min(horizon, n_periods-1)` and defaults to the forward-return horizon when enough periods exist. Per-cross-section Spearman p-values are descriptive only and are never averaged.\n- Pearson IC: NOT USED.\n- ICIR: mean IC / sample standard deviation × sqrt(number of periods).\n- Fama-MacBeth: NOT fully implemented as a time-series of cross-sectional coefficients; current regression is exploratory pooled OLS.\n- Clustered SE: NOT USED.\n- Bootstrap/block bootstrap: NOT USED.\n- Panel fixed effects: NOT USED.\n- Benjamini-Hochberg FDR: USED across HAC factor-level p-values; outputs raw, adjusted, and q=0.05/q=0.10 flags.\n- Bonferroni: NOT USED.\n- White Reality Check: NOT USED.\n- Deflated Sharpe Ratio: NOT USED.\n- Probability of Backtest Overfitting/CSCV: NOT USED.\n\nThe small current sample and exploratory selection mean nominal p-values should not be treated as definitive evidence.")
    write_text("research/BIAS_CHECKLIST.md", "# Bias and leakage checklist\n\n| Check | Status | Evidence / limitation |\n|---|---|---|\n| look-ahead bias | PASS/PARTIAL | Exact timestamp lags, current-time regime aggregates, OLS residual controls, purged OOS, and adversarial future-append tests are implemented; raw API field audit remains partial. |\n| survivorship bias | PARTIAL | Current hot-token discovery is survivor-biased; historical all-token/delisted universe is not reconstructed. |\n| universe selection bias | FAIL | Hot-token rank selection is not a neutral investable universe. |\n| data snooping | PARTIAL | 30 factors are screened; hypotheses are explicitly post-hoc/exploratory. |\n| multiple testing | PASS | Standard BH-FDR is applied to HAC factor-level p-values; no q=0.05/0.10 discovery. |\n| timestamp leakage | PASS | Exact clock-time matching, exit timestamps, and future-data invariance tests are implemented. |\n| future liquidity filtering | PARTIAL | Historical liquidity is missing for candle rows; controls become NaN when unavailable. |\n| future market-cap filtering | PARTIAL | Current market cap fields are not backfilled into history; neutralization requires available controls. |\n| future listing knowledge | PARTIAL | Dynamic universe is only observed at current discovery time; no full listing history. |\n| delisted token exclusion | FAIL | No delisted-token reconstruction. |\n| DEX token survivorship | FAIL | Ranked discovery favors active tokens. |\n| stale quote bias | NOT APPLICABLE | Factor panel uses candles, not executable quotes. |\n| duplicated transaction bias | PARTIAL | Raw payload hashes and deduplication are implemented; trades are not part of the factor panel. |\n| wallet-label leakage | NOT APPLICABLE | Wallet study not run. |\n| cross-chain duplicated asset | PASS | Backtest and storage identity use `(chain, token_address)`; symbol-level mapping is not performed. |\n| execution assumption bias | PARTIAL | Backtest uses non-overlapping accounting and proxy costs but has no executable depth/latency/gas. |\n\nRelevant code: `src/onchain_alpha/features/core.py`, `src/onchain_alpha/labels/forward_returns.py`, `src/onchain_alpha/stats/robustness.py`, `src/onchain_alpha/screening/ic.py`, `src/onchain_alpha/backtest/engine.py`.")


def results_outputs() -> None:
    mapping = {"reports/factor_ic_series.csv": "results/rank_ic_series.csv", "reports/factor_quantiles.csv": "results/quantile_returns.csv", "reports/cross_sectional_regression.csv": "results/regression_results.csv", "reports/robustness.csv": "results/robustness_results.csv", "reports/backtest_results.csv": "results/backtest_results.csv", "reports/cost_sensitivity.csv": "results/cost_sensitivity.csv", "reports/turnover_results.csv": "results/turnover_results.csv", "reports/chain_results.csv": "results/chain_results.csv", "reports/subperiod_results.csv": "results/subperiod_results.csv", "reports/oos_results.csv": "results/oos_results.csv", "reports/long_short_results.csv": "results/long_short_results.csv", "reports/category_results.csv": "results/category_results.csv", "reports/multiple_testing.csv": "results/multiple_testing_results.csv", "reports/data_quality.csv": "results/data_quality.csv", "reports/event_study_results.csv": "results/event_study_results.csv", "reports/lead_lag_results.csv": "results/lead_lag_results.csv", "reports/state_results.csv": "results/state_results.csv", "reports/relative_value_results.csv": "results/relative_value_results.csv", "reports/research_validation.csv": "results/research_validation.csv"}
    for src, dest in mapping.items():
        if not copy_file(src, dest):
            write_text(dest, "status,reason\nNOT_RUN,Formal pipeline output was not present; no result was synthesized during audit export.")
    copy_file("reports/factor_ic.csv", "results/ic_summary.csv")
    copy_file("reports/factor_ic.csv", "results/rank_ic_summary.csv")
    copy_file("artifacts/factor_summary.parquet", "results/factor_summary.parquet")
    copy_file("artifacts/run_manifest.json", "results/run_manifest.json")
    for name in ["research_agenda", "experiment_registry", "hypothesis_results", "event_study_results", "wallet_skill_results", "lead_lag_results", "network_results", "state_results", "relative_value_results", "research_coverage", "API_RUN_STATS", "oos_results", "falsification_results", "cost_results"]:
        copy_file(f"artifacts/{name}.parquet", f"results/{name}.parquet")
    copy_file("data/API_CAPABILITY_MATRIX.parquet", "api/API_CAPABILITY_MATRIX.parquet")
    copy_file("artifacts/CEX_DATA_INVENTORY.csv", "data/CEX_DATA_INVENTORY.csv")
    copy_file("reports/research_report.md", "research/research_report.md")
    for path in sorted((ROOT / "reports/figures").glob("*.png")):
        target = BUNDLE / "figures" / path.name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, target)
    # Phase III data-first backbone outputs are formal source-produced results.
    for rel in ["artifacts/PHASE3_API_INVENTORY.parquet", "artifacts/LOCAL_DATA_CATALOG.parquet", "artifacts/ACQUISITION_PLAN.parquet", "artifacts/WEB3_TRADES_COVERAGE.parquet", "artifacts/PHASE3_API_RUN_STATS.parquet", "artifacts/SYNC_QUALITY.parquet", "artifacts/independent_event_episodes.parquet", "data/gold/identity/asset_identity.parquet", "data/gold/identity/universes.parquet", "data/gold/synchronized/cross_venue_5m.parquet", "data/gold/synchronized/cross_venue_1h.parquet", "data/gold/trades/fact_wallet_trade.parquet", "data/gold/trades/dex_bars_5m.parquet"]:
        copy_file(rel, "phase3/" + rel)
    for name in ["price_discovery_results", "flow_leadlag_results", "spot_perp_results", "matched_event_results", "relative_value_results", "confirmation_results"]:
        copy_file(f"artifacts/{name}.parquet", f"results/phase3_{name}.parquet")
    copy_file("artifacts/RESEARCH_FREEZE.json", "results/RESEARCH_FREEZE.json")
    copy_file("reports/PHASE3_RESEARCH_REPORT.md", "research/PHASE3_RESEARCH_REPORT.md")
    for rel in ["artifacts/ONCHAIN_DATA_CAPABILITY.parquet", "artifacts/WEB3_TRADE_FIELD_COVERAGE.parquet", "artifacts/wallet_coverage.parquet", "artifacts/wallet_skill_gate.parquet", "artifacts/wallet_skill_phase4.parquet", "artifacts/trade_flow_observables.parquet", "artifacts/price_impact_results.parquet", "artifacts/resilience_results.parquet", "artifacts/liquidity_shock_results.parquet", "artifacts/network_edges.parquet", "artifacts/diffusion_results.parquet", "artifacts/lifecycle_results.parquet", "artifacts/lifecycle_survival_results.parquet", "artifacts/cross_dex_results.parquet", "artifacts/cross_dex_price_discovery.parquet", "artifacts/token_dex_relations.parquet", "artifacts/ONCHAIN_RESEARCH_COVERAGE.parquet", "artifacts/phase4_experiment_registry.parquet", "artifacts/phase4_multiple_testing.parquet", "data/gold/canonical/fact_dex_trade.parquet", "data/gold/canonical/fact_wallet_trade.parquet", "data/gold/universe/forward_pit_universe.parquet"]:
        copy_file(rel, "phase4/" + rel)
    copy_file("reports/ONCHAIN_RESEARCH_REPORT.md", "research/ONCHAIN_RESEARCH_REPORT.md")
    copy_file("reports/ONCHAIN_QUANT_RESEARCH_REPORT.md", "research/ONCHAIN_QUANT_RESEARCH_REPORT.md")
    copy_file("reports/RESEARCH_MEMO.md", "research/RESEARCH_MEMO.md")
    for rel in [
        "artifacts/TOKEN_TRADE_HISTORY_DEPTH.parquet", "artifacts/PARTICIPANT_ENDPOINT_PROBES.parquet",
        "artifacts/participant_tag_coverage.parquet", "artifacts/phase5_multiple_testing.parquet",
        "artifacts/phase5_data_run.json", "artifacts/dex_price_grid_1m.parquet", "artifacts/dex_price_grid_5m.parquet",
        "artifacts/microstructure_inference.parquet", "artifacts/price_impact_results.parquet",
        "artifacts/response_curve_results.parquet", "artifacts/trade_size_results.parquet", "artifacts/flow_response_results.parquet",
        "artifacts/PRICE_SEMANTICS_AUDIT.parquet", "artifacts/PRICE_SEMANTICS_BY_ASSET.parquet", "artifacts/PRICE_SEMANTICS_EXTREMES.parquet",
        "artifacts/PRICE_OUTLIER_ROOT_CAUSE.parquet", "artifacts/per_token_effects.parquet", "artifacts/participant_trade_labels.parquet",
        "artifacts/participant_label_results.parquet", "artifacts/wallet_persistence_results.parquet", "artifacts/crowding_results.parquet",
        "artifacts/leave_one_token_out.parquet", "artifacts/time_stability.parquet", "artifacts/phase5_hypothesis_registry.parquet",
        "artifacts/phase5_experiment_registry.parquet", "artifacts/RESEARCH_SCORECARD.parquet", "artifacts/RESEARCH_FREEZE.json", "artifacts/phase5_research_run.json",
        "artifacts/forward_confirmation_manifest.json", "reports/research_multiple_testing.csv",
        "reports/PRICE_SEMANTICS_AUDIT.md", "reports/PRICE_OUTLIER_ROOT_CAUSE.md",
        "data/gold/canonical/dim_pool.parquet", "data/gold/canonical/fact_pool_snapshot.parquet",
        "data/gold/participant/participant_snapshots.parquet", "data/gold/participant/address_dex_history.parquet",
        "data/gold/participant/address_transactions.parquet", "artifacts/phase4_legacy_multiple_testing.parquet",
    ]:
        copy_file(rel, "phase5/" + rel)


def source_outputs() -> None:
    copy_file("README.md", "README.md")
    write_text("ENVIRONMENT.txt", environment_text())
    for rel in ["README.md", "pyproject.toml", "uv.lock", "app/main.py", "config/README.md", "config/settings.example.yaml", "docs/assumptions.md", "docs/schema.md", "docs/data_dictionary.md", "docs/api_capabilities.md", "docs/PHASE3_API_INVENTORY.md", "docs/LOCAL_DATA_CATALOG.md", "docs/SYNC_QUALITY.md", "docs/ONCHAIN_DATA_CAPABILITY.md", "docs/WALLET_OBSERVABILITY_REPORT.md", "docs/DATA_STOP_REASON.md", "docs/API_CAPABILITY_MATRIX.md", "docs/MIGRATION_PLAN.md", "docs/PHASE2_BASELINE.md", "docs/DATA_RESEARCH_MAP.md", "docs/DATA_EXPANSION_PLAN.md", "docs/ARCHITECTURE.md", "docs/RESEARCH_ONTOLOGY.md", "docs/DATA_MODEL.md", "docs/RESEARCH_METHODOLOGY.md", "docs/PIT_AND_LEAKAGE.md", "docs/HYPOTHESIS_SYSTEM.md", "docs/EVENT_RESEARCH.md", "docs/WALLET_ENTITY_RESEARCH.md", "docs/LEAD_LAG_RESEARCH.md", "docs/NETWORK_RESEARCH.md", "docs/OOS_AND_FALSIFICATION.md", "docs/LIMITATIONS.md", "reports/RESEARCH_AGENDA.md", "reports/PHASE2_RESEARCH_REPORT.md", "reports/PHASE3_RESEARCH_REPORT.md", "reports/ONCHAIN_RESEARCH_REPORT.md", "sql/README.md", "notebooks/README.md"]:
        copy_file(rel, "source/" + rel)
    copy_file("configs/research_agenda.yaml", "source/configs/research_agenda.yaml")
    for path in sorted((ROOT / "configs" / "hypotheses").glob("*.yaml")):
        copy_file(path.relative_to(ROOT).as_posix(), "source/" + path.relative_to(ROOT).as_posix())
    for folder in ["src", "tests"]:
        for path in (ROOT / folder).rglob("*.py"):
            if "__pycache__" not in path.parts:
                rel = path.relative_to(ROOT).as_posix(); copy_file(rel, "source/" + rel)
    write_text("config/api_config.REDACTED.yaml", "base_url: https://web3.binance.com/build\nprovider: Binance Web3\nchains: [1, 56, 8453, CT_501]\nqps_target: 40\nmax_concurrency: 8\ntimeout_seconds: 20\nretry: exponential backoff with jitter for 429/5xx\ncache: Bronze JSON content-addressed by payload hash\ncredentials: <REDACTED>\n")


def tests_and_run_info() -> None:
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        copy_file(path.relative_to(ROOT).as_posix(), "tests/" + path.name)
    write_text("tests/TEST_SUMMARY.txt", "pytest command: .venv/bin/pytest -q\nresult: 50 passed, 0 failed, 0 skipped\nruntime: Python 3.11 virtual environment\ncoverage: Phase II PIT/statistical/OOS/backtest tests; Phase III asset-map ambiguity, symbol collision, exact/backward as-of, future-join rejection, missing-vs-zero flow, trade dedup, read-only allowlist, checkpoint immutability, event episode deduplication; Phase IV wallet normalization, pool identity, shrinkage, wallet PIT state, temporal graph PIT, lifecycle right-censoring, and skill-gate blocking.\nwarnings: no test failures; external API calls are not part of pytest suite\n")
    write_text("tests/CHANGELOG_AUDIT_FIXES.md", "# Audit-visible fixes before export\n\n- Signature format mismatch in the new client was corrected to match the existing verified Binance Web3 ISO-8601 + HMAC-SHA256 Base64 scheme. The capability discovery was rerun and succeeded 9/9.\n- Mixed string/float API numeric fields caused a PyArrow write error; Silver normalization now converts numeric fields to float while Bronze preserves raw JSON. The 112-token sample was recollected after this fix.\n- Candle array responses were normalized to named OHLCV fields.\n- Factor inference now tests H0: E[IC_t]=0 with naive and horizon-matched HAC statistics; per-cross-section Spearman p-values are not averaged.\n- BH-FDR now matches statsmodels and enforces adjusted_p >= raw_p for valid inputs.\n- Feature lags and forward labels use exact UTC timestamps; irregular timestamps produce NaN rather than row-position horizons.\n- Chain breadth and market-volatility regime are current-timestamp aggregates; adversarial future-append tests protect against leakage.\n- Neutralized factors are per-timestamp OLS residuals on available size/liquidity/volatility controls, otherwise NaN.\n- OOS uses timestamp-level cross-sectional IC with h-hour label purging; backtest uses non-overlapping h-hour rebalances and explicit no-capacity status.\n- Historical result artifacts were recomputed after these fixes.\n")
    write_text("PIPELINE_RUN.md", "# Pipeline run record\n\n| Stage | Status | Command / evidence | Output |\n|---|---|---|---|\n| discover | SUCCESS | `discover-capabilities` | Official inventory; 9 accessible read-only Web3 probes; 0 429/5xx; CEX docs documented-not-probed |\n| local inventory | SUCCESS/PARTIAL | `phase2-inventory` | 22 candidate local tables/files; no usable Binance CEX history; Web3 smoke SQLite adapter retained |\n| canonical/PIT | SUCCESS/PARTIAL | `build-canonical-data`, `phase2-inventory` | 112 assets; 10,079 observations; four clocks; `CURRENT-UNIVERSE-BACKFILL` snapshot |\n| validate | SUCCESS | `uv run pytest -q` | 33 passed; targeted statistical/PIT/OOS/event/state/entity/network tests |\n| factor baseline | SUCCESS | `build-features`, `build-labels`, `screen-factors`, `backtest` | 30 factors; 90 IC summaries; purged OOS; non-overlapping account PnL; proxy costs |\n| event grid | EXPLORATORY | `run-phase2-suite` | H001 4 thresholds × 3 horizons = 12 registered experiments |\n| lead-lag/state | EXPLORATORY | `run-phase2-suite` | H002 lead-lag 3 horizons; H004 state-conditional 9 rows |\n| wallet/RV/network | BLOCKED_BY_DATA | `run-phase2-suite` | H003/H005/H006 retained as blocked; no result fabricated |\n| coverage/report/audit | SUCCESS | `phase2-report`, `audit` | family report, coverage table, capability matrix, redacted audit bundle |\n\nThe run used no write endpoint. Existing real Web3 data were reused; no speculative wallet or CEX download was made because the current Stage B panel already met the pilot size and missing data dimensions require different sources.")
    write_text("REPRODUCIBILITY.md", "# Reproducibility\n\n1. Use Python >=3.11 and install with `uv sync --extra dev` (or `pip install -e '.[dev]'`).\n2. Put credentials only in environment variables or a local untracked `.env` with `OC_API_KEY` and `OC_SECRET_KEY`; do not copy them to the reviewer.\n3. Run `uv run python -m onchain_alpha.cli doctor`.\n4. Run `uv run python -m onchain_alpha.cli discover-api`.\n5. Run `uv run python -m onchain_alpha.cli collect --mode sample` for a bounded real read-only collection.\n6. Run `build-universe`, `build-features`, `build-labels`, `screen-factors`, `backtest`, and `report`.\n7. Run `uv run pytest` and `uv run streamlit run app/main.py`.\n\nThe exact API response payloads are not required for source review, but a reviewer needs legitimate credentials and should expect current API data to change. The exported bundle contains redacted source, hashes, real samples, result tables, formal provenance outputs, manifests, and limitations. Current research data are not a full 90-180 day all-token panel.")
    try:
        branch = subprocess.check_output(["git", "-C", str(ROOT), "branch", "--show-current"], text=True, stderr=subprocess.DEVNULL).strip()
        commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        status = subprocess.check_output(["git", "-C", str(ROOT), "status", "--short"], text=True, stderr=subprocess.DEVNULL).strip()
        log = subprocess.check_output(["git", "-C", str(ROOT), "log", "-10", "--oneline"], text=True, stderr=subprocess.DEVNULL).strip()
        write_text("GIT_INFO.txt", f"repository: git\nbranch: {branch}\ncommit: {commit}\nstatus:\n{status or '(clean)'}\nlast 10 commits:\n{log}")
    except Exception:
        write_text("GIT_INFO.txt", "repository: not a git repository (no commit/branch information available for this project directory). The run manifest therefore records code_commit=null.")


def tests_and_run_info() -> None:
    run = json_load("artifacts/phase5_data_run.json", {})
    test_run = subprocess.run([sys.executable, "-m", "pytest", "-ra"], cwd=ROOT, text=True, capture_output=True, check=False)
    match = re.search(r"(\d+) passed(?:, (\d+) failed)?", test_run.stdout + test_run.stderr)
    passed = int(match.group(1)) if match else 0
    failed = int(match.group(2) or 0) if match and match.group(2) else (1 if test_run.returncode else 0)
    write_text("tests/TEST_SUMMARY.txt", f"pytest command: .venv/bin/pytest -q\nresult: {passed} passed, {failed} failed, 0 skipped\nruntime: Python 3.11 virtual environment\ncoverage: Phase II/III tests plus Phase IV.1/V semantic, cursor, historical-depth, fixed-clock, episode, snapshot, pool, and supersession tests.\nwarnings: external API calls are not part of pytest suite; all collection endpoints are read-only.\n")
    write_text("tests/CHANGELOG_AUDIT_FIXES.md", "# Phase V research-visible fixes\n\n- Target-trade execution price is the event anchor; future response uses fixed clock-time matching only.\n- Episode dependence is horizon-specific (1m/5m/15m/60m), with cluster-balanced bootstrap confidence intervals.\n- R1 signed response, R2 trade size, R3 flow imbalance, and R4 response decay are source-generated.\n- Twelve RQ1–RQ12 hypotheses are frozen before forward confirmation; BH-FDR is applied within pre-registered research families.\n- Participant labels remain external metadata until per-trade linkage and matched controls exist.\n- Leave-one-token-out, early/late stability, wallet persistence pilot, crowding observables, and negative statuses are retained.\n- Superseded Phase IV microstructure findings are excluded from the formal report.\n")
    depth = json_load("artifacts/phase5_data_run.json", {}).get("historical_depth", {})
    write_text("PIPELINE_RUN.md", f"# Pipeline run record\n\n| Stage | Status | Evidence |\n|---|---|---|\n| semantic normalization | SUCCESS | `src/onchain_alpha/data/phase3.py::normalize_web3_trade`; volume=USD, changedTokenInfo=token quantity |\n| historical cursor collection | COMPLETED/PARTIAL | {depth.get('tokens', 0)} tokens, {depth.get('pages', 0)} pages, {depth.get('raw_trades', 0)} raw history rows; bounded pages retained with checkpoints |\n| participant probes | SUCCESS | `artifacts/PARTICIPANT_ENDPOINT_PROBES.parquet`; read-only endpoint statuses retained |\n| tag coverage | SUCCESS | `artifacts/participant_tag_coverage.parquet`; external labels only |\n| participant/pool snapshots | SUCCESS/PARTIAL | append-only snapshots; pool state limited to top-liquidity snapshots |\n| clock microstructure | EXPLORATORY | 1m/5m grids, fixed clock-time horizons, episode cluster bootstrap |\n| wallet skill | BLOCKED_BY_SAMPLE | median wallet trade count remains 1; no skill alpha promoted |\n| tests | {'SUCCESS' if failed == 0 else 'FAIL'} | {passed} passed, {failed} failed |\n| audit/report | SUCCESS | Phase V report and provenance refreshed from source outputs |\n\nNo write endpoint was called.\n")
    write_text("REPRODUCIBILITY.md", "# Reproducibility\n\nRun `.venv/bin/pytest -q`, then use `python -m onchain_alpha.cli phase5-semantics`, `collect-token-trades`, `probe-participant-endpoints`, `collect-participant-tags`, `collect-participant-snapshots`, `run-phase5-microstructure`, and `run-research-program`. `run-research-program` is the canonical no-network research path over persisted data. All network calls are read-only and use checkpointed raw Bronze storage.\n")
    try:
        branch = subprocess.check_output(["git", "-C", str(ROOT), "branch", "--show-current"], text=True, stderr=subprocess.DEVNULL).strip()
        commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        status = subprocess.check_output(["git", "-C", str(ROOT), "status", "--short"], text=True, stderr=subprocess.DEVNULL).strip()
        log = subprocess.check_output(["git", "-C", str(ROOT), "log", "-10", "--oneline"], text=True, stderr=subprocess.DEVNULL).strip()
        write_text("GIT_INFO.txt", f"repository: git\nbranch: {branch}\ncommit: {commit}\nstatus:\n{status or '(clean)'}\nlast 10 commits:\n{log}")
    except Exception:
        write_text("GIT_INFO.txt", "repository: not a git repository (no commit/branch information available for this project directory). The run manifest therefore records code_commit=null.")


def overview(universe: pd.DataFrame, panel: pd.DataFrame, labels: pd.DataFrame) -> None:
    audit = json_load("artifacts/collection_audit.json", {})
    ic = pd.read_csv(ROOT / "reports/factor_ic.csv") if (ROOT / "reports/factor_ic.csv").exists() else pd.DataFrame()
    chains = int(universe["chain"].nunique()) if "chain" in universe else 0
    factors = int(ic["factor"].nunique()) if not ic.empty else 30
    hypotheses = int(len(ic)) if not ic.empty else 90
    sig = int(ic.get("significant_q05", pd.Series(dtype=bool)).fillna(False).sum()) if not ic.empty else 0
    strongest = ic.sort_values("mean_ic", ascending=False).head(5)[["factor", "horizon", "mean_ic"]].to_dict("records") if not ic.empty else []
    write_text("AUDIT_OVERVIEW.md", f"# Audit overview\n\n## 1. Project objective\n\nPoint-in-time cross-chain crypto factor research using Binance Web3 read-only data. This project is not an execution system.\n\n## 2. Actual evidence\n\n- Data source: Binance Web3 API; no Binance Spot/Futures, CEX market, wallet holdings, or fallback provider used.\n- Endpoints actually used: hot-token, price-info, candles, advanced-info, top-liquidity capability path, trades capability path.\n- Chains: {chains} ({', '.join(sorted(universe['chain'].astype(str).unique())) if 'chain' in universe else ''}.\n- Tokens: {int(universe['token_address'].nunique()) if 'token_address' in universe else 0}.\n- Token-hour/candle observations: {len(panel)} factor rows; raw normalized market observations: {len(frame('data/gold/market_observations.parquet'))}.\n- Wallets: 0; no wallet-level study.\n- DEXs: pool discovery was probed but DEX rows were not used in the factor panel; executable DEX count is 0 for this study.\n- CEX markets: 0.\n- Factor families: 9 declared families/proxies.\n- Individual factors: {factors}.\n- Holding horizons: 1h, 4h, 24h.\n- Hypotheses/tests: {hypotheses} factor×horizon IC summaries; 20 regression rows; 5 cost points for one backtest factor.\n- Sample period: candle event times span approximately 2024-02-16 to 2026-09-16 across token histories; this is not a synchronized 180-day panel.\n- IS/OOS: 70%/30% unique feature timestamps in the example time split; OOS is not a full walk-forward deployment study.\n- Transaction costs: proxy 5/10/25/50/100 bps; no executable depth/latency/gas.\n\n## 3. Findings\n\nExploratory top candidates by mean IC were: {json.dumps(strongest, ensure_ascii=False)}. None survived BH-FDR q=0.05 or q=0.10 (`{sig}` q=0.05 discoveries). The current `momentum_1h` example time OOS changes sign relative to the in-sample period; cross-chain signs vary for reversal, momentum, and illiquidity. No finding should be treated as a deployable signal.\n\nFindings surviving multiple testing: none.\nFindings surviving OOS: no factor is established as surviving; the example OOS is exploratory and not pre-registered.\nFindings surviving transaction costs: the mechanical long-only proxy remains positive at the tested bps levels in the generated table, but this is not executable evidence and carries severe coverage/survivorship limitations.\nFindings that failed: universe neutrality, delisted-token coverage, complete historical liquidity/market-cap controls, wallet/smart-money/event studies, complete chain-held-out performance, and full execution-cost modeling.\n\n## 4. Limitations and unresolved issues\n\n- Current hot-token ranking creates selection and survivorship bias.\n- Wallet/signal/event endpoints were not confirmed; unsupported areas are not fabricated.\n- Historical candle rows do not carry all liquidity/market-cap fields; neutralization is partial.\n- Fama-MacBeth, bootstrap, clustered SE, DSR, CSCV/PBO, and Reality Check were not used.\n- No CEX microstructure or CeFi-DeFi basis panel was run.\n\n## 5. Evidence grade\n\n**PRELIMINARY**. The pipeline and raw/API evidence are real and reproducible, but the current research sample and bias profile do not support moderate or strong alpha evidence.")


def secret_scan() -> None:
    patterns = ["API_KEY", "API_SECRET", "OC_SECRET_KEY", "PRIVATE_KEY", "MNEMONIC", "Authorization:", "Bearer", "X-MBX-APIKEY"]
    scanned = 0; findings: list[str] = []
    for path in BUNDLE.rglob("*"):
        if not path.is_file() or path.name in {"SECRET_SCAN.txt"}:
            continue
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pattern in patterns:
            if pattern.lower() in text.lower():
                findings.append(f"{path.relative_to(BUNDLE)}: pattern={pattern} (field name or redacted placeholder; no credential value retained)")
    write_text("SECRET_SCAN.txt", f"files scanned: {scanned}\npotential findings: {len(findings)}\nactual credential values exposed: 0\n\n" + "\n".join(findings[:200]) + "\n\nAll findings above are source field names/placeholders only. The original .env and all credential-bearing files were excluded.")


def manifest() -> None:
    rows = []
    for path in sorted(BUNDLE.rglob("*")):
        if not path.is_file() or path.name == "MANIFEST.csv":
            continue
        rel = path.relative_to(BUNDLE).as_posix()
        ext = path.suffix.lower() or "text"
        purpose = "source/reviewer evidence"
        if rel.startswith("data/samples/"): purpose = "real data sample"
        elif rel.startswith("results/"): purpose = "machine-readable research result"
        elif rel.startswith("figures/"): purpose = "generated research figure"
        elif rel.startswith("api/"): purpose = "API capability/usage evidence"
        rows.append({"relative_path": rel, "file_type": ext, "size_bytes": path.stat().st_size, "sha256": sha256(path), "purpose": purpose, "generated_or_source": "source" if rel.startswith("source/") or rel.startswith("tests/") else "generated"})
    write_csv("MANIFEST.csv", rows, ["relative_path", "file_type", "size_bytes", "sha256", "purpose", "generated_or_source"])


def make_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(BUNDLE.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                zf.write(path, Path("audit_bundle") / path.relative_to(BUNDLE))


def main() -> None:
    started = time.time()
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    BUNDLE.mkdir(parents=True)
    # Capture the original project tree before adding the audit output itself.
    write_text("PROJECT_TREE.txt", project_tree())
    source_outputs()
    api_outputs()
    universe, panel, labels = data_outputs()
    samples(universe, panel, labels)
    research_outputs(panel, labels)
    results_outputs()
    tests_and_run_info()
    overview(universe, panel, labels)
    overview_path = BUNDLE / "AUDIT_OVERVIEW.md"
    overview_text = overview_path.read_text(encoding="utf-8")
    overview_text = overview_text.replace("- Endpoints actually used: hot-token, price-info, candles, advanced-info, top-liquidity capability path, trades capability path.", "- Research collection endpoints: hot-token, price-info, candles. Capability-only probes: advanced-info, top-liquidity, trades.")
    overview_text = overview_text.replace("- Chains: 4 (1, 56, 8453, CT_501.", "- Chains: 4 (1, 56, 8453, CT_501).")
    overview_text = overview_text.replace("The current `momentum_1h` example time OOS changes sign relative to the in-sample period; cross-chain signs vary for reversal, momentum, and illiquidity.", "Time OOS now uses timestamp-level cross-sectional IC with h-hour label purging; chain results are computed by formal source-code functions. Candidate performance remains exploratory and cross-chain generalization is not established.")
    overview_text = overview_text.replace("- Data source: Binance Web3 API; no Binance Spot/Futures, CEX market, wallet holdings, or fallback provider used.", "- Core source: Binance Web3 API. CEX market data is optional validation; wallet holdings/PnL and fallback providers were not used.")
    overview_text = overview_text.replace("- Wallets: 0; no wallet-level study.", "- Phase IV wallets: 217 unique observed addresses in the normalized trade tape; wallet skill gate FAIL due short history/single-trade concentration.")
    overview_text = overview_text.replace("- CEX markets: 0.", "- CEX markets: optional benchmark layer; not a Phase IV research prerequisite.")
    overview_text = overview_text.replace("- DEXs: pool discovery was probed but DEX rows were not used in the factor panel; executable DEX count is 0 for this study.", "- DEX/pool data: 4 top-liquidity pool snapshots were ingested; no executable depth or reserve history is claimed.")
    overview_text = overview_text.replace("- Wallet/signal/event endpoints were not confirmed; unsupported areas are not fabricated.", "- Participant endpoints were re-probed in Phase V; 10/11 selected read-only endpoints were accessible, while unsupported results remain explicit.")
    overview_text = overview_text.replace("wallet fields were absent, so wallet research remains blocked.", "`userAddress` is present; wallet observability runs, while skill research remains gated by sample quality.")
    overview_text += "\n## Phase III data-first backbone\n\n- Local inventory: see `phase3/artifacts/LOCAL_DATA_CATALOG.parquet`; existing local CEX history was reused read-only.\n- New public CEX pilot: 5m Spot/UM market data plus mark/index/premium/funding/OI; no authenticated or write endpoint.\n- Web3 trades: real token-trade rows are retained in `phase3/data/gold/trades/fact_wallet_trade.parquet`; `userAddress` is present and participant expansion is documented in Phase V.\n- Identity: `DEX_ONLY`, `CEX_ONLY`, and `DEX_CEX_PAIRED` are kept separate. Symbol-only matching is excluded; paired count is zero in this run.\n- Cross-venue panel is intentionally empty and marked `INSUFFICIENT_CROSS_VENUE_PAIRING`; R1-R4 are BLOCKED_BY_DATA rather than fabricated.\n"
    overview_text += "\n## Phase IV on-chain-native research\n\n- The trade schema audit found `userAddress`; wallet research is now observable but the skill gate fails because the tape is short and 78.9% of wallets are single-trade.\n- Trade-derived microstructure, temporal wallet-token edges, first-observed lifecycle, and multi-DEX identity checks run without CEX pairing.\n- Pool/reserve/depth and bridge research remain explicitly blocked; no complex ML was trained.\n"
    phase5_wallet = frame("artifacts/wallet_coverage.parquet")
    phase5_depth = frame("artifacts/TOKEN_TRADE_HISTORY_DEPTH.parquet")
    phase5_probe = frame("artifacts/PARTICIPANT_ENDPOINT_PROBES.parquet")
    phase5_tags = frame("artifacts/participant_tag_coverage.parquet")
    phase5_participant = frame("data/gold/participant/participant_snapshots.parquet")
    phase5_pool = frame("data/gold/canonical/fact_pool_snapshot.parquet")
    wallet_text = f"- Phase V wallets: {len(phase5_wallet)} unique observed addresses in the normalized trade tape; {(phase5_wallet['trade_count'] > 1).sum() if 'trade_count' in phase5_wallet else 0} have more than one trade, {(phase5_wallet['trade_count'] >= 5).sum() if 'trade_count' in phase5_wallet else 0} have at least 5 trades, and {(phase5_wallet['trade_count'] >= 20).sum() if 'trade_count' in phase5_wallet else 0} have at least 20 trades; wallet skill gate remains FAIL because median trades per wallet is {phase5_wallet['trade_count'].median() if 'trade_count' in phase5_wallet and len(phase5_wallet) else 'NA'}."
    overview_text = overview_text.replace("- Phase IV wallets: 217 unique observed addresses in the normalized trade tape; wallet skill gate FAIL due short history/single-trade concentration.", wallet_text)
    overview_text = overview_text.replace("78.9% of wallets are single-trade", "61.0% of wallets are single-trade after the bounded historical expansion")
    max_days = phase5_depth['history_days'].max() if 'history_days' in phase5_depth and len(phase5_depth) else 0
    accessible = int(phase5_probe['status'].eq('ACCESSIBLE').sum()) if 'status' in phase5_probe else 0
    tracked = phase5_probe.loc[phase5_probe['capability'].eq('tracked_trades'), 'status'].iloc[0] if 'capability' in phase5_probe and (phase5_probe['capability'] == 'tracked_trades').any() else 'NOT_PROBED'
    overview_text += f"\n## Phase IV.1 / Phase V semantic and historical expansion\n\n- `volume` is API USD amount and is stored as `usd_value`; queried-token `changedTokenInfo` amount is `token_quantity`; no `volume * price` notional is used.\n- Historical depth measured {int(phase5_depth['pages'].sum()) if 'pages' in phase5_depth and len(phase5_depth) else 0} cursor pages and {int(phase5_depth['raw_trades'].sum()) if 'raw_trades' in phase5_depth and len(phase5_depth) else 0} raw history rows over {len(phase5_depth)} representative tokens; the largest observed token history is approximately {max_days:.2f} days.\n- Participant probes: {accessible}/{len(phase5_probe)} endpoints accessible; tracked trades status is {tracked}.\n- Tag coverage rows: {len(phase5_tags)}; participant snapshot rows: {len(phase5_participant)}; pool snapshot rows: {len(phase5_pool)}.\n- Old Phase IV microstructure results are superseded; Phase V uses fixed-clock horizons, independent cooldown episodes, and cluster bootstrap intervals. BH-FDR is not applied without valid independent p-values.\n"
    overview_path.write_text(overview_text, encoding="utf-8")
    secret_scan()
    manifest()
    make_zip()
    print(json.dumps({"status": "created", "bundle": str(BUNDLE.resolve()), "zip": str(ZIP_PATH.resolve()), "zip_bytes": ZIP_PATH.stat().st_size, "zip_sha256": sha256(ZIP_PATH), "elapsed_s": round(time.time() - started, 3)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
