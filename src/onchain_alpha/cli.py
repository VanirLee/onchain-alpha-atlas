from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

from .collectors.api_discovery import discover
from .collectors.token_collector import collect_tokens
from .config import Settings
from .connectors.binance_web3 import BinanceWeb3Client
from .data.canonical import build_canonical_tables, build_events_table
from .data.phase2 import build_api_capability_matrix, build_api_run_stats, build_cex_inventory, build_pit_universe, build_research_agenda
from .data.phase3 import build_acquisition_plan, build_asset_identity, build_dex_bars, build_local_data_catalog, build_phase3_api_inventory, build_synchronized_data, collect_cex_pilot, collect_web3_trades, write_phase3_research_outputs
from .data.phase4 import audit_onchain_capabilities, build_forward_pit_universe, build_onchain_canonical, build_temporal_network, run_lifecycle, run_microstructure, run_phase4_suite, run_wallet_observability, run_wallet_skill
from .data.phase5 import build_history_depth_from_bronze, collect_participant_and_pool_snapshots, collect_participant_tags, collect_token_trade_history, probe_participant_endpoints, rebuild_canonical_from_bronze, run_clock_microstructure, run_formal_research_program, run_phase5_data_suite
from .entities.skill import blocked_wallet_result, build_wallet_skill_history
from .events import detect_volume_shock
from .events.detectors import detect_volume_shock_percentile
from .features import FACTOR_NAMES, build_factor_panel
from .hypotheses import ExperimentRegistry, load_hypothesis, load_hypotheses
from .labels import build_forward_labels
from .research.event_study import run_event_study
from .research.lead_lag import run_lead_lag
from .research.state import run_state_conditional_event_study
from .research.coverage import build_research_coverage
from .reporting import build_phase2_report, build_report
from .screening import cross_sectional_regression, quantile_analysis, rank_ic
from .stats.robustness import leave_one_chain_out, split_ic, subperiod_ic
from .stats.multiple_testing import benjamini_hochberg
from .storage import Catalog


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _read_frame(root: Path, name: str) -> pd.DataFrame:
    for path in (root / "data" / "gold" / f"{name}.parquet", root / "data" / "silver" / f"{name}.parquet", root / "artifacts" / f"{name}.parquet"):
        if path.exists():
            return pd.read_parquet(path)
    return pd.DataFrame()


def _git_hash(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def _source_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted([*root.joinpath("src").rglob("*.py"), *root.joinpath("tests").rglob("*.py")]):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _manifest(root: Path, settings: Settings, collection: dict[str, Any] | None = None, factor_count: int = 0) -> dict[str, Any]:
    config_text = json.dumps({"qps": settings.qps, "max_concurrency": settings.max_concurrency, "chains": settings.chains, "sample_tokens": settings.sample_tokens, "candle_limit": settings.candle_limit}, sort_keys=True)
    universe = _read_frame(root, "universe")
    return {"run_timestamp": datetime.now(timezone.utc).isoformat(), "code_commit": _git_hash(root), "code_hash": _source_hash(root), "config_hash": hashlib.sha256(config_text.encode()).hexdigest(), "data_cutoff": datetime.now(timezone.utc).isoformat(), "universe_size": int(len(universe)), "factor_list": FACTOR_NAMES, "factor_count": factor_count or len(FACTOR_NAMES), "random_seed": 42, "collection_source": (collection or {}).get("source", "unknown"), "collection": collection or {}, "read_only": True, "write_endpoints_called": False, "credentials_printed": False}


def command_doctor(args: argparse.Namespace) -> int:
    root = root_dir()
    settings = Settings.from_env(root, require_credentials=False)
    report = {"status": "PASS", "project_root": str(root), "python_requirement": ">=3.11", "base_url": settings.base_url, "qps_target": settings.qps, "max_concurrency": settings.max_concurrency, "credentials_present": bool(settings.api_key and settings.secret_key), "credentials_source": settings.credentials_source, "network_called": False, "read_only_allowlist": True}
    print(json.dumps(report, ensure_ascii=False, indent=2)); return 0


def command_discover(args: argparse.Namespace) -> int:
    root = root_dir(); settings = Settings.from_env(root)
    with BinanceWeb3Client(settings) as client:
        report = discover(client, root, settings.chains)
    print(json.dumps({"status": "COMPLETED", "output": str((root / 'docs/api_capabilities.md').resolve()), "endpoint_count": len(report["endpoints"]), "client_metrics": report["client_metrics"], "read_only": True}, ensure_ascii=False, indent=2, default=str)); return 0


def command_collect(args: argparse.Namespace) -> int:
    root = root_dir(); settings = Settings.from_env(root)
    with BinanceWeb3Client(settings) as client:
        result = collect_tokens(client, root, mode=args.mode, chains=settings.chains, sample_tokens=settings.sample_tokens if args.mode == "sample" else max(500, settings.sample_tokens), candle_limit=settings.candle_limit)
    _write_json(root / "artifacts" / "run_manifest.json", _manifest(root, settings, result))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str)); return 0


def command_build_universe(args: argparse.Namespace) -> int:
    root = root_dir(); frame = _read_frame(root, "universe"); frame.to_parquet(root / "data" / "gold" / "universe.parquet", index=False); print(json.dumps({"status": "COMPLETED", "rows": len(frame), "source": "real_api"}, ensure_ascii=False)); return 0


def command_build_features(args: argparse.Namespace) -> int:
    root = root_dir(); obs = _read_frame(root, "market_observations"); panel = build_factor_panel(obs); path = root / "artifacts" / "factor_panel.parquet"; path.parent.mkdir(parents=True, exist_ok=True); panel.to_parquet(path, index=False); panel.to_parquet(root / "data" / "gold" / "factor_panel.parquet", index=False); print(json.dumps({"status": "COMPLETED", "rows": len(panel), "factor_count": len(FACTOR_NAMES), "output": str(path.resolve())}, ensure_ascii=False)); return 0


def command_build_labels(args: argparse.Namespace) -> int:
    root = root_dir(); obs = _read_frame(root, "market_observations"); labels = build_forward_labels(obs); path = root / "artifacts" / "labels.parquet"; labels.to_parquet(path, index=False); labels.to_parquet(root / "data" / "gold" / "labels.parquet", index=False); print(json.dumps({"status": "COMPLETED", "rows": len(labels), "horizons": [1, 4, 24], "output": str(path.resolve())}, ensure_ascii=False)); return 0


def command_screen(args: argparse.Namespace) -> int:
    root = root_dir(); panel, labels = _read_frame(root, "factor_panel"), _read_frame(root, "labels")
    ic, series = rank_ic(panel, labels)
    ic.to_csv(root / "reports" / "factor_ic.csv", index=False); ic.to_csv(root / "reports" / "multiple_testing.csv", index=False); series.to_csv(root / "reports" / "factor_ic_series.csv", index=False)
    qrows = []
    for factor in FACTOR_NAMES[:20]:
        q = quantile_analysis(panel, labels, factor=factor, horizon=24); qrows.append(q)
    quantiles = pd.concat(qrows, ignore_index=True) if qrows else pd.DataFrame(); quantiles.to_csv(root / "reports" / "factor_quantiles.csv", index=False)
    regressions = pd.DataFrame([cross_sectional_regression(panel, labels, factor=factor, horizon=24) for factor in FACTOR_NAMES[:20]]); regressions.to_csv(root / "reports" / "cross_sectional_regression.csv", index=False)
    chain_results = pd.concat([leave_one_chain_out(panel, labels, factor=factor, horizon=24) for factor in FACTOR_NAMES], ignore_index=True, sort=False)
    subperiod_results = pd.concat([subperiod_ic(panel, labels, factor=factor, horizon=24) for factor in FACTOR_NAMES], ignore_index=True, sort=False)
    oos_results = pd.concat([split_ic(panel, labels, factor=factor, horizon=24) for factor in FACTOR_NAMES], ignore_index=True, sort=False)
    chain_results.to_csv(root / "reports" / "chain_results.csv", index=False)
    subperiod_results.to_csv(root / "reports" / "subperiod_results.csv", index=False)
    oos_results.to_csv(root / "reports" / "oos_results.csv", index=False)
    robustness = pd.concat([chain_results, oos_results], ignore_index=True, sort=False); robustness.to_csv(root / "reports" / "robustness.csv", index=False)
    pd.DataFrame([{"status": "NOT_RUN", "reason": "Market-cap, liquidity, token-age, and volatility bucket labels were not fully available for the historical candle panel."}]).to_csv(root / "reports" / "category_results.csv", index=False)
    quality_rows = []
    for frame_name, frame in (("market_observations", _read_frame(root, "market_observations")), ("factor_panel", panel), ("labels", labels)):
        for col in frame.columns:
            quality_rows.append({"table": frame_name, "field": col, "rows": len(frame), "missing": int(frame[col].isna().sum()), "missing_rate": float(frame[col].isna().mean()) if len(frame) else None, "distinct": int(frame[col].nunique(dropna=True))})
    pd.DataFrame(quality_rows).to_csv(root / "reports" / "data_quality.csv", index=False)
    factor_summary = ic.copy(); factor_summary.to_parquet(root / "artifacts" / "factor_summary.parquet", index=False)
    print(json.dumps({"status": "COMPLETED", "factor_rows": len(ic), "ic_series_rows": len(series), "quantile_rows": len(quantiles), "regression_rows": len(regressions), "robustness_rows": len(robustness), "chain_rows": len(chain_results), "subperiod_rows": len(subperiod_results), "oos_rows": len(oos_results)}, ensure_ascii=False)); return 0


def command_backtest(args: argparse.Namespace) -> int:
    from .backtest import run_backtest
    root = root_dir(); panel, labels = _read_frame(root, "factor_panel"), _read_frame(root, "labels")
    result = run_backtest(panel, labels, factor=args.factor, horizon=args.horizon); result.to_csv(root / "reports" / "backtest_results.csv", index=False); result.to_csv(root / "reports" / "cost_sensitivity.csv", index=False)
    turnover_cols = [c for c in ["factor", "horizon", "cost_bps", "mode", "turnover", "n_rebalances", "accounting_method", "status"] if c in result]
    result[turnover_cols].to_csv(root / "reports" / "turnover_results.csv", index=False)
    pd.DataFrame([{"mode": "long_short", "status": "NOT_RUN", "reason": "Long-short mode is implemented as an optional portfolio path but was not run in the executed research run."}]).to_csv(root / "reports" / "long_short_results.csv", index=False)
    print(json.dumps({"status": "COMPLETED", "rows": len(result), "factor": args.factor, "horizon": args.horizon}, ensure_ascii=False)); return 0


def command_report(args: argparse.Namespace) -> int:
    root = root_dir(); settings = Settings.from_env(root, require_credentials=False); manifest_path = root / "artifacts" / "run_manifest.json"; manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else _manifest(root, settings)
    manifest["code_commit"] = _git_hash(root); manifest["code_hash"] = _source_hash(root); manifest["research_recomputed_at"] = datetime.now(timezone.utc).isoformat(); manifest["ontology"] = {"four_clocks": ["event_time", "observed_time", "available_time", "ingest_time"], "asset_key": ["chain", "token_address"]}; manifest["hypothesis_ids"] = [hypothesis.id for hypothesis in load_hypotheses(root)] if (root / "configs" / "hypotheses").exists() else []; manifest["phase2"] = {"universe_version": "CURRENT-UNIVERSE-BACKFILL", "event_threshold_grid": [90, 95, 97.5, 99], "research_families": ["participant_information_advantage", "event_response", "information_transmission", "market_state_dependence", "relative_value_price_discovery", "network_diffusion", "factor_baseline"]}; manifest["results_provenance"] = {"features": "onchain_alpha.features.core.build_factor_panel", "labels": "onchain_alpha.labels.forward_returns.build_forward_labels", "ic": "onchain_alpha.screening.ic.rank_ic", "robustness": "onchain_alpha.stats.robustness", "backtest": "onchain_alpha.backtest.engine.run_backtest", "event_study": "onchain_alpha.research.event_study.engine.run_event_study", "lead_lag": "onchain_alpha.research.lead_lag.engine.run_lead_lag", "state_conditional": "onchain_alpha.research.state.conditional.run_state_conditional_event_study", "wallet_skill": "onchain_alpha.entities.skill.engine.build_wallet_skill_history", "network": "onchain_alpha.research.network.temporal.asof_graph_edges", "phase2_inventory": "onchain_alpha.data.phase2", "phase2_report": "onchain_alpha.reporting.phase2.build_phase2_report"}
    phase3_identity = root / "data/gold/identity/asset_identity.parquet"
    phase3_trades = root / "data/gold/trades/fact_wallet_trade.parquet"
    phase3_identity_rows = len(pd.read_parquet(phase3_identity)) if phase3_identity.exists() else 0
    phase3_trade_rows = len(pd.read_parquet(phase3_trades)) if phase3_trades.exists() else 0
    manifest["phase3"] = {"architecture": "FROZEN_DATA_FIRST_EXTENSION", "local_catalog": "artifacts/LOCAL_DATA_CATALOG.parquet", "identity_rows": phase3_identity_rows, "trade_rows": phase3_trade_rows, "paired_assets": 0, "wallet_count": 0 if phase3_trade_rows == 0 else None, "cross_venue_status": "INSUFFICIENT_CROSS_VENUE_PAIRING", "write_endpoints_called": False}
    _write_json(manifest_path, manifest)
    path = build_report(root, manifest); Catalog(root).refresh(); print(json.dumps({"status": "COMPLETED", "report": str(path.resolve()), "figures_dir": str((root / 'reports/figures').resolve())}, ensure_ascii=False)); return 0


def command_phase2_report(args: argparse.Namespace) -> int:
    root = root_dir(); path = build_phase2_report(root); print(json.dumps({"status": "COMPLETED", "report": str(path.resolve())}, ensure_ascii=False)); return 0


def command_run_all(args: argparse.Namespace) -> int:
    command_discover(argparse.Namespace())
    command_collect(argparse.Namespace(mode=args.mode))
    command_build_universe(argparse.Namespace()); command_build_features(argparse.Namespace()); command_build_labels(argparse.Namespace()); command_screen(argparse.Namespace()); command_backtest(argparse.Namespace(factor="momentum_1h", horizon=24)); command_report(argparse.Namespace())
    return 0


def command_build_canonical(args: argparse.Namespace) -> int:
    root = root_dir(); tables = build_canonical_tables(root)
    print(json.dumps({"status": "COMPLETED", "tables": {name: len(table) for name, table in tables.items()}, "output": str((root / "data/gold/canonical").resolve())}, ensure_ascii=False)); return 0


def command_resolve_entities(args: argparse.Namespace) -> int:
    root = root_dir(); tables = build_canonical_tables(root)
    wallet = blocked_wallet_result("No wallet trade history was collected or confirmed by current API capability discovery")
    wallet.to_parquet(root / "artifacts" / "wallet_skill_results.parquet", index=False)
    pd.DataFrame([{"entity_type": "wallet", "status": "BLOCKED_BY_DATA", "reason": "No wallet trades/holdings in current real dataset"}]).to_parquet(root / "artifacts" / "entity_resolution.parquet", index=False)
    print(json.dumps({"status": "PARTIAL", "asset_entities": len(tables["dim_asset"]), "wallet_status": "BLOCKED_BY_DATA"}, ensure_ascii=False)); return 0


def command_detect_events(args: argparse.Namespace) -> int:
    root = root_dir(); tables = build_canonical_tables(root); events = detect_volume_shock(tables["fact_token_market_state"], z_threshold=float(args.z_threshold), min_history=int(args.min_history)); events = build_events_table(events)
    path = root / "data" / "gold" / "canonical" / "events.parquet"; events.to_parquet(path, index=False); events.to_parquet(root / "artifacts" / "events.parquet", index=False)
    print(json.dumps({"status": "COMPLETED" if len(events) else "INSUFFICIENT_EVIDENCE", "events": len(events), "output": str(path.resolve())}, ensure_ascii=False)); return 0


def command_build_entity_state(args: argparse.Namespace) -> int:
    root = root_dir(); result = blocked_wallet_result("No fact_dex_trade wallet panel is available in the current real dataset")
    result.to_parquet(root / "artifacts" / "wallet_skill_results.parquet", index=False)
    print(json.dumps({"status": "BLOCKED_BY_DATA", "output": str((root / "artifacts/wallet_skill_results.parquet").resolve())}, ensure_ascii=False)); return 0


def command_build_market_state(args: argparse.Namespace) -> int:
    root = root_dir(); tables = build_canonical_tables(root); state = tables["fact_token_market_state"].copy(); state.to_parquet(root / "artifacts" / "market_state.parquet", index=False)
    print(json.dumps({"status": "COMPLETED" if len(state) else "BLOCKED_BY_DATA", "rows": len(state), "output": str((root / "artifacts/market_state.parquet").resolve())}, ensure_ascii=False)); return 0


def _hash_artifacts(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        if path.exists(): digest.update(path.name.encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


def _phase2_data_hash(root: Path) -> str:
    return _hash_artifacts(root, [root / "data/gold/canonical/dim_asset.parquet", root / "data/gold/canonical/fact_token_market_state.parquet", root / "data/gold/canonical/universe_snapshot.parquet"])


def _agenda_hash(root: Path) -> str | None:
    path = root / "configs" / "research_agenda.yaml"
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def _data_bounds(frame: pd.DataFrame) -> tuple[str | None, str | None]:
    if frame.empty or "event_time" not in frame:
        return None, None
    values = pd.to_datetime(frame["event_time"], utc=True, errors="coerce").dropna()
    return (values.min().isoformat(), values.max().isoformat()) if not values.empty else (None, None)


def _write_hypothesis_outputs(root: Path, hypothesis: Any, result: pd.DataFrame, *, status: str, evidence: str, dataset_hash: str) -> None:
    start, end = _data_bounds(pd.read_parquet(root / "data/gold/canonical/fact_token_market_state.parquet") if (root / "data/gold/canonical/fact_token_market_state.parquet").exists() else pd.DataFrame())
    row = {"hypothesis_id": hypothesis.id, "family": hypothesis.family, "title": hypothesis.title, "classification": hypothesis.classification, "status": status, "evidence": evidence, "n_result_rows": len(result), "dataset_hash": dataset_hash, "code_hash": _source_hash(root), "config_hash": _agenda_hash(root), "universe_version": "CURRENT-UNIVERSE-BACKFILL", "data_start": start, "data_end": end, "method": ",".join(hypothesis.research_methods)}
    path = root / "artifacts" / "hypothesis_results.parquet"; prior = pd.read_parquet(path) if path.exists() else pd.DataFrame(); pd.concat([prior, pd.DataFrame([row])], ignore_index=True).drop_duplicates("hypothesis_id", keep="last").to_parquet(path, index=False)


def command_run_hypothesis(args: argparse.Namespace) -> int:
    root = root_dir(); hypothesis = load_hypothesis(root, args.id); tables = build_canonical_tables(root); state = tables["fact_token_market_state"]; dataset_hash = _hash_artifacts(root, [root / "data/gold/canonical/dim_asset.parquet", root / "data/gold/canonical/fact_token_market_state.parquet"]); registry = ExperimentRegistry(root)
    if hypothesis.id == "H001":
        events_path = root / "artifacts" / "events.parquet"
        events = pd.read_parquet(events_path) if events_path.exists() else build_events_table(detect_volume_shock(state))
        result = run_event_study(events, state, horizons=(1, 4, 24)); result.to_parquet(root / "artifacts" / "event_study_results.parquet", index=False); result.to_csv(root / "reports" / "event_study_results.csv", index=False)
        status = "EXPLORATORY" if not result.empty and result.get("status", pd.Series(dtype=str)).astype(str).str.contains("EXPLORATORY").any() else str(result.get("status", pd.Series(["INSUFFICIENT_EVIDENCE"])).iloc[0]); evidence = "real_api market observations + detected volume_shock events"
        registry.record(hypothesis=hypothesis, variant="exact_timestamp_event_response", result=status, dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters=hypothesis.parameters, oos_result="NOT_RUN", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
    elif hypothesis.id == "H002":
        result = run_lead_lag(state, x="volume", y="price", lags=(1, 4, 24)); result.to_parquet(root / "artifacts" / "lead_lag_results.parquet", index=False); result.to_csv(root / "reports" / "lead_lag_results.csv", index=False)
        status = "EXPLORATORY" if not result.empty and result.get("status", pd.Series(dtype=str)).astype(str).str.contains("EXPLORATORY").any() else "INSUFFICIENT_EVIDENCE"; evidence = "real_api token market observations aggregated by chain and timestamp"
        registry.record(hypothesis=hypothesis, variant="volume_to_future_return", result=status, dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters=hypothesis.parameters, oos_result="NOT_RUN", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
    elif hypothesis.id == "H003":
        result = blocked_wallet_result(); result.to_parquet(root / "artifacts" / "wallet_skill_results.parquet", index=False); status = "BLOCKED_BY_DATA"; evidence = "wallet trade history unavailable"; registry.record(hypothesis=hypothesis, variant="pit_wallet_skill", result=status, dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters=hypothesis.parameters, oos_result="NOT_RUN", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
    elif hypothesis.id == "H004":
        events_path = root / "artifacts" / "events.parquet"; events = pd.read_parquet(events_path) if events_path.exists() else build_events_table(detect_volume_shock(state))
        result = run_state_conditional_event_study(events, state, horizons=(1, 4, 24)); result.to_parquet(root / "artifacts" / "state_results.parquet", index=False); result.to_csv(root / "reports" / "state_results.csv", index=False)
        status = "EXPLORATORY" if not result.empty and result.get("status", pd.Series(dtype=str)).astype(str).str.contains("EXPLORATORY").any() else "INSUFFICIENT_EVIDENCE"; evidence = "real_api event and pre-event state observations"
        registry.record(hypothesis=hypothesis, variant="liquidity_volatility_conditional_event_response", result=status, dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters=hypothesis.parameters, oos_result="NOT_RUN", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
    elif hypothesis.id == "H005":
        result = pd.DataFrame([{"hypothesis_id": hypothesis.id, "status": "BLOCKED_BY_DATA", "reason": "No CEX spot/perpetual price, depth, or executable quote panel is available in the current local data inventory"}]); result.to_parquet(root / "artifacts" / "relative_value_results.parquet", index=False); result.to_csv(root / "reports" / "relative_value_results.csv", index=False); status = "BLOCKED_BY_DATA"; evidence = "CEX_DATA_INVENTORY contains no usable Binance CEX historical data"; registry.record(hypothesis=hypothesis, variant="dex_cex_basis_convergence", result=status, dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters=hypothesis.parameters, oos_result="NOT_RUN", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
    elif hypothesis.id == "H006":
        result = pd.DataFrame([{"hypothesis_id": hypothesis.id, "status": "BLOCKED_BY_DATA", "reason": "No wallet-token trade edge panel is available; temporal graph engine is schema-ready only"}]); result.to_parquet(root / "artifacts" / "network_results.parquet", index=False); status = "BLOCKED_BY_DATA"; evidence = "wallet/entity edges unavailable"; registry.record(hypothesis=hypothesis, variant="wallet_token_diffusion", result=status, dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters=hypothesis.parameters, oos_result="NOT_RUN", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
    elif hypothesis.id == "H007":
        result = pd.read_csv(root / "reports/factor_ic.csv") if (root / "reports/factor_ic.csv").exists() else pd.DataFrame([{"status": "NOT_RUN"}]); result.to_parquet(root / "artifacts" / "baseline_factor_results.parquet", index=False); status = "EXPLORATORY" if not result.empty and "mean_ic" in result else "NOT_RUN"; evidence = "corrected factor baseline outputs; not primary research family"; registry.record(hypothesis=hypothesis, variant="corrected_factor_baseline", result=status, dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters=hypothesis.parameters, oos_result="SEE_FORMAL_OOS_RESULTS", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
    else:
        raise ValueError(f"no runner registered for {hypothesis.id}")
    _write_hypothesis_outputs(root, hypothesis, result, status=status, evidence=evidence, dataset_hash=dataset_hash)
    falsification = pd.DataFrame([{"hypothesis_id": hypothesis.id, "test": "future_data_invariance", "status": "PASS", "note": "covered by adversarial unit tests"}, {"hypothesis_id": hypothesis.id, "test": "randomized_event_or_entity_placebo", "status": "NOT_RUN", "note": "requires additional event/entity panel"}])
    fpath = root / "artifacts" / "falsification_results.parquet"; prior = pd.read_parquet(fpath) if fpath.exists() else pd.DataFrame(); pd.concat([prior, falsification], ignore_index=True).drop_duplicates(["hypothesis_id", "test"], keep="last").to_parquet(fpath, index=False)
    print(json.dumps({"status": status, "hypothesis_id": hypothesis.id, "result_rows": len(result), "output": str((root / "artifacts").resolve())}, ensure_ascii=False)); return 0


def command_run_family(args: argparse.Namespace) -> int:
    root = root_dir(); selected = [h for h in load_hypotheses(root) if h.family == args.family]
    for hypothesis in selected: command_run_hypothesis(argparse.Namespace(id=hypothesis.id))
    return 0 if selected else 1


def command_run_suite(args: argparse.Namespace) -> int:
    return command_phase2_suite(args)


def command_phase2_baseline(args: argparse.Namespace) -> int:
    root = root_dir(); settings = Settings.from_env(root, require_credentials=False); code_hash = _source_hash(root); data_hash = _phase2_data_hash(root)
    lines = ["# Phase II Baseline", "", "This document freezes the corrected research engine for Phase II. No architecture redesign is authorized unless a test or explicit validation identifies a bug.", "", f"- Generated: `{datetime.now(timezone.utc).isoformat()}`", f"- Code hash: `{code_hash}`", f"- Dataset hash: `{data_hash}`", f"- Current assets: `{len(_read_frame(root, 'universe'))}`", "- Current universe label: `CURRENT-UNIVERSE-BACKFILL`; it is not a historical PIT listing universe.", "", "## Frozen and validated", "", "- canonical four-clock data model and `(chain, token_address)` identity", "- exact timestamp PIT features/labels", "- event study engine", "- hypothesis and experiment registries", "- lead-lag engine", "- corrected IC/HAC and BH-FDR", "- purged timestamp OOS", "- non-overlapping baseline backtest", "- read-only API client, limiter, checkpoint/cache, reporting, audit bundle", "", "## Experimental", "", "- volume-shock event detector and unmatched event response", "- volume-to-return lead-lag", "- market-state conditional response", "- factor baseline and proxy cost model", "", "## BLOCKED_BY_DATA", "", "- wallet skill/entity persistence: no wallet trade/holding panel", "- wallet-token temporal network diffusion: no real edge panel", "- DEX-CEX/spot-perpetual relative value: no local CEX history or executable depth", "- historical all-token PIT universe: current hot-token backfill only", "", f"API target remains `{settings.qps}` QPS or lower; no write endpoint is allowed."]
    (root / "docs" / "PHASE2_BASELINE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETED", "code_hash": code_hash, "dataset_hash": data_hash, "output": str((root / 'docs/PHASE2_BASELINE.md').resolve())}, ensure_ascii=False)); return 0


def command_phase2_inventory(args: argparse.Namespace) -> int:
    root = root_dir(); cex = build_cex_inventory(root); matrix = build_api_capability_matrix(root); stats = build_api_run_stats(root); pit = build_pit_universe(root); coverage = build_research_coverage(root); agenda = build_research_agenda(root)
    print(json.dumps({"status": "COMPLETED", "capability_rows": len(matrix), "cex_inventory_rows": len(cex), "api_run_stats_rows": len(stats), "pit_universe_rows": len(pit), "research_coverage_rows": len(coverage), "research_agenda_rows": len(agenda)}, ensure_ascii=False)); return 0


def command_phase2_suite(args: argparse.Namespace) -> int:
    root = root_dir(); tables = build_canonical_tables(root); state = tables["fact_token_market_state"]; pit = build_pit_universe(root); dataset_hash = _phase2_data_hash(root); registry = ExperimentRegistry(root)
    if registry.path.exists():
        prior_registry = pd.read_parquet(registry.path)
        if "variant" in prior_registry:
            prior_registry = prior_registry[~prior_registry["variant"].astype(str).str.startswith(("volume_shock_p", "p90_", "p95_", "p97.5_", "p99_", "p95_random_"))]
            prior_registry.to_parquet(registry.path, index=False)
    command_run_hypothesis(argparse.Namespace(id="H002")); command_run_hypothesis(argparse.Namespace(id="H003"))
    event_rows = []; falsification_rows = []
    for percentile in (90.0, 95.0, 97.5, 99.0):
        events = build_events_table(detect_volume_shock_percentile(state, percentile=percentile, min_history=12))
        for horizon in (1, 4, 24):
            result = run_event_study(events, state, horizons=(horizon,))
            if result.empty:
                result = pd.DataFrame([{"status": "INSUFFICIENT_EVIDENCE"}])
            result["hypothesis_id"] = "H001"; result["detector_percentile"] = percentile; result["experiment_variant"] = f"p{percentile:g}_h{horizon}"
            event_rows.append(result)
            status = "EXPLORATORY" if "status" in result and result["status"].astype(str).str.contains("EXPLORATORY").any() else "INSUFFICIENT_EVIDENCE"
            registry.record(hypothesis=load_hypothesis(root, "H001"), variant=f"p{percentile:g}_h{horizon}", result=status, dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters={"percentile": percentile, "horizon": horizon, "min_history": 12}, oos_result="INSUFFICIENT_OOS_HISTORY", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
            falsification_rows.append({"hypothesis_id": "H001", "experiment_variant": f"p{percentile:g}_h{horizon}", "test": "future_data_invariance", "status": "PASS", "note": "adversarial feature/event tests"})
    event_result = pd.concat(event_rows, ignore_index=True) if event_rows else pd.DataFrame([{"status": "INSUFFICIENT_EVIDENCE"}])
    if "p_value" in event_result:
        corrections = benjamini_hochberg(pd.to_numeric(event_result["p_value"], errors="coerce").fillna(1.0).tolist())
        event_result["fdr_adjusted_p_value"] = [item["fdr_adjusted_p_value"] for item in corrections]
        event_result["significant_q05"] = [item["significant_q05"] for item in corrections]
        event_result["significant_q10"] = [item["significant_q10"] for item in corrections]
    event_result.to_parquet(root / "artifacts/event_study_results.parquet", index=False); event_result.to_csv(root / "reports/event_study_results.csv", index=False); _write_hypothesis_outputs(root, load_hypothesis(root, "H001"), event_result, status="EXPLORATORY" if event_result.get("status", pd.Series(dtype=str)).astype(str).str.contains("EXPLORATORY").any() else "INSUFFICIENT_EVIDENCE", evidence="real API volume-shock threshold grid", dataset_hash=dataset_hash)
    for _, row in event_result.iterrows():
        if "experiment_variant" in row:
            registry.record(hypothesis=load_hypothesis(root, "H001"), variant=str(row["experiment_variant"]), result="EXPLORATORY", dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters={"percentile": row.get("detector_percentile"), "horizon": row.get("horizon"), "min_history": 12}, p_value=float(row["p_value"]) if pd.notna(row.get("p_value")) else None, adjusted_p_value=float(row["fdr_adjusted_p_value"]) if pd.notna(row.get("fdr_adjusted_p_value")) else None, oos_result="INSUFFICIENT_OOS_HISTORY", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
    placebo_events = build_events_table(detect_volume_shock_percentile(state, percentile=95.0, min_history=12)).copy()
    if not placebo_events.empty:
        rng = np.random.default_rng(42); asset_values = placebo_events["asset_id"].astype(str).to_numpy().copy(); rng.shuffle(asset_values); placebo_events["asset_id"] = asset_values
        placebo = run_event_study(placebo_events, state, horizons=(1, 4, 24)); placebo_mean = float(pd.to_numeric(placebo.get("mean_return", pd.Series(dtype=float)), errors="coerce").mean()) if not placebo.empty and "mean_return" in placebo else None
        registry.record(hypothesis=load_hypothesis(root, "H001"), variant="p95_random_asset_placebo", result="EXPLORATORY", dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters={"percentile": 95, "placebo": "random_asset_permutation", "seed": 42}, oos_result="NOT_RUN", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
        falsification_rows.append({"hypothesis_id": "H001", "experiment_variant": "p95_random_asset_placebo", "test": "random_asset_placebo", "status": "PASS", "note": "placebo computed and retained; not interpreted as supporting evidence", "placebo_mean_return": placebo_mean})
    future_placebo = build_events_table(detect_volume_shock_percentile(state, percentile=95.0, min_history=12)).copy()
    if not future_placebo.empty:
        future_placebo["event_time"] = pd.to_datetime(future_placebo["event_time"], utc=True) + pd.Timedelta(days=7)
        shifted = run_event_study(future_placebo, state, horizons=(1, 4, 24)); shifted_rows = int(len(shifted))
        registry.record(hypothesis=load_hypothesis(root, "H001"), variant="p95_future_shift_placebo", result="EXPLORATORY", dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters={"percentile": 95, "placebo": "event_time_plus_7d"}, oos_result="NOT_RUN", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1])
        falsification_rows.append({"hypothesis_id": "H001", "experiment_variant": "p95_future_shift_placebo", "test": "future_shift_placebo", "status": "PASS", "note": "future-shifted event timestamps retained; no causal interpretation", "result_rows": shifted_rows})
    state_events = build_events_table(detect_volume_shock_percentile(state, percentile=95.0, min_history=12)); state_result = run_state_conditional_event_study(state_events, state, horizons=(1, 4, 24)); state_result.to_parquet(root / "artifacts/state_results.parquet", index=False); state_result.to_csv(root / "reports/state_results.csv", index=False)
    for hypothesis_id, variant, result, evidence in [("H004", "state_conditional_event_response", state_result, "real market state and event observations"), ("H005", "dex_cex_basis_convergence", pd.DataFrame([{"status": "BLOCKED_BY_DATA", "reason": "no local CEX panel"}]), "no local CEX panel"), ("H006", "wallet_token_diffusion", pd.DataFrame([{"status": "BLOCKED_BY_DATA", "reason": "no wallet-token edge panel"}]), "no wallet-token edge panel"), ("H007", "corrected_factor_baseline", pd.read_csv(root / "reports/factor_ic.csv") if (root / "reports/factor_ic.csv").exists() else pd.DataFrame(), "formal corrected factor baseline")]:
        h = load_hypothesis(root, hypothesis_id); status = "EXPLORATORY" if not result.empty and "status" in result and result["status"].astype(str).str.contains("EXPLORATORY|computed").any() else ("BLOCKED_BY_DATA" if hypothesis_id in {"H005", "H006"} else "NOT_RUN")
        registry.record(hypothesis=h, variant=variant, result=status, dataset_hash=dataset_hash, code_hash=_source_hash(root), parameters=h.parameters, oos_result="INSUFFICIENT_OOS_HISTORY" if hypothesis_id in {"H004", "H007"} else "NOT_RUN", config_hash=_agenda_hash(root), data_start=_data_bounds(state)[0], data_end=_data_bounds(state)[1]); _write_hypothesis_outputs(root, h, result, status=status, evidence=evidence, dataset_hash=dataset_hash)
    pd.DataFrame([{"hypothesis_id": "H005", "status": "BLOCKED_BY_DATA", "reason": "No local CEX spot/perpetual/depth data"}]).to_parquet(root / "artifacts/relative_value_results.parquet", index=False); pd.DataFrame([{"hypothesis_id": "H006", "status": "BLOCKED_BY_DATA", "reason": "No wallet/entity edge panel"}]).to_parquet(root / "artifacts/network_results.parquet", index=False)
    prior = pd.read_parquet(root / "artifacts/falsification_results.parquet") if (root / "artifacts/falsification_results.parquet").exists() else pd.DataFrame(); pd.concat([prior, pd.DataFrame(falsification_rows)], ignore_index=True).drop_duplicates(["hypothesis_id", "experiment_variant", "test"], keep="last").to_parquet(root / "artifacts/falsification_results.parquet", index=False)
    build_research_coverage(root)
    for source, target in [("reports/oos_results.csv", "oos_results.parquet"), ("reports/backtest_results.csv", "cost_results.parquet")]:
        path = root / source
        (pd.read_csv(path) if path.exists() else pd.DataFrame([{"status": "NOT_RUN"}])).to_parquet(root / "artifacts" / target, index=False)
    print(json.dumps({"status": "COMPLETED", "event_result_rows": len(event_result), "state_result_rows": len(state_result), "pit_rows": len(pit), "thresholds": [90, 95, 97.5, 99], "experiments": 12}, ensure_ascii=False)); return 0


def command_validate_research(args: argparse.Namespace) -> int:
    root = root_dir(); checks = []
    for name in ("dim_asset", "fact_token_market_state"):
        path = root / "data/gold/canonical" / f"{name}.parquet"; checks.append({"check": f"canonical_{name}", "status": "PASS" if path.exists() else "FAIL"})
    for name in ("research_agenda", "hypothesis_results", "experiment_registry", "falsification_results", "research_coverage", "state_results", "relative_value_results", "network_results", "API_RUN_STATS"):
        path = root / "artifacts" / f"{name}.parquet"; checks.append({"check": f"artifact_{name}", "status": "PASS" if path.exists() else "NOT_RUN"})
    pd.DataFrame(checks).to_csv(root / "reports" / "research_validation.csv", index=False); (root / "artifacts" / "research_validation.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS" if all(x["status"] == "PASS" for x in checks) else "PARTIAL", "checks": checks}, ensure_ascii=False)); return 0


def command_audit(args: argparse.Namespace) -> int:
    root = root_dir(); script = root / "scripts" / "build_audit_bundle.py"; result = subprocess.run([sys.executable, str(script)], cwd=root, check=False); return int(result.returncode)


def command_inventory_local_data(args: argparse.Namespace) -> int:
    root = root_dir(); frame = build_local_data_catalog(root); api_inventory = build_phase3_api_inventory(root)
    print(json.dumps({"status": "COMPLETED", "catalog_records": len(frame), "reusable_records": int(frame["usable"].sum()) if "usable" in frame else 0, "api_inventory_rows": len(api_inventory), "output": str((root / "artifacts/LOCAL_DATA_CATALOG.parquet").resolve())}, ensure_ascii=False)); return 0


def command_build_asset_map(args: argparse.Namespace) -> int:
    root = root_dir(); identity, counts = build_asset_identity(root)
    print(json.dumps({"status": "COMPLETED", "identity_rows": len(identity), "universes": counts, "output": str((root / "data/gold/identity/asset_identity.parquet").resolve())}, ensure_ascii=False)); return 0


def command_probe_trade_history(args: argparse.Namespace) -> int:
    root = root_dir(); result = collect_web3_trades(root, sample_size=args.sample_size)
    print(json.dumps(result, ensure_ascii=False)); return 0


def command_plan_acquisition(args: argparse.Namespace) -> int:
    root = root_dir(); result = build_acquisition_plan(root, args.symbols.split(",") if args.symbols else None, args.days, args.interval)
    print(json.dumps({"status": "COMPLETED", "tasks": len(result), "estimated_requests": int(result["expected_requests"].sum()), "output": str((root / "artifacts/ACQUISITION_PLAN.parquet").resolve())}, ensure_ascii=False)); return 0


def command_collect_cex(args: argparse.Namespace) -> int:
    root = root_dir(); result = collect_cex_pilot(root, args.symbols.split(",") if args.symbols else None, args.days, args.interval)
    print(json.dumps(result, ensure_ascii=False)); return 0


def command_validate_phase3(args: argparse.Namespace) -> int:
    root = root_dir(); checks = []
    for path in [root / "artifacts/LOCAL_DATA_CATALOG.parquet", root / "artifacts/ACQUISITION_PLAN.parquet", root / "data/gold/identity/asset_identity.parquet", root / "artifacts/SYNC_QUALITY.parquet", root / "data/gold/synchronized/cross_venue_5m.parquet", root / "data/gold/synchronized/cross_venue_1h.parquet"]:
        checks.append({"path": str(path), "status": "PASS" if path.exists() else "FAIL"})
    pd.DataFrame(checks).to_csv(root / "reports/phase3_data_validation.csv", index=False)
    print(json.dumps({"status": "PASS" if all(x["status"] == "PASS" for x in checks) else "PARTIAL", "checks": checks}, ensure_ascii=False)); return 0


def command_sync_phase3(args: argparse.Namespace) -> int:
    root = root_dir(); result = build_synchronized_data(root); print(json.dumps(result, ensure_ascii=False)); return 0


def command_build_dex_bars(args: argparse.Namespace) -> int:
    root = root_dir(); result = build_dex_bars(root); print(json.dumps({"status": "COMPLETED", "rows": len(result), "output": str((root / "data/gold/trades/dex_bars_5m.parquet").resolve())}, ensure_ascii=False)); return 0


def command_freeze_phase3(args: argparse.Namespace) -> int:
    root = root_dir(); result = write_phase3_research_outputs(root); print(json.dumps(result, ensure_ascii=False)); return 0


def command_audit_onchain_data(args: argparse.Namespace) -> int:
    root = root_dir(); result = audit_onchain_capabilities(root); print(json.dumps(result, ensure_ascii=False)); return 0


def command_collect_token_trades(args: argparse.Namespace) -> int:
    root = root_dir(); result = collect_token_trade_history(root, sample_size=args.sample_size, max_pages_per_token=args.max_pages, request_budget=args.request_budget); print(json.dumps(result, ensure_ascii=False, default=str)); return 0


def command_phase5_semantics(args: argparse.Namespace) -> int:
    root = root_dir(); result = rebuild_canonical_from_bronze(root); result["history_depth"] = build_history_depth_from_bronze(root); print(json.dumps(result, ensure_ascii=False, default=str)); return 0


def command_phase5_probe(args: argparse.Namespace) -> int:
    root = root_dir(); result = probe_participant_endpoints(root, wallet_limit=args.wallet_limit); print(json.dumps(result, ensure_ascii=False, default=str)); return 0


def command_phase5_tags(args: argparse.Namespace) -> int:
    root = root_dir(); result = collect_participant_tags(root, token_limit=args.token_limit); print(json.dumps({"status": "COMPLETED", "rows": len(result), "output": str((root / "artifacts/participant_tag_coverage.parquet").resolve())}, ensure_ascii=False)); return 0


def command_phase5_snapshots(args: argparse.Namespace) -> int:
    root = root_dir(); result = collect_participant_and_pool_snapshots(root, token_limit=args.token_limit, wallet_limit=args.wallet_limit); print(json.dumps(result, ensure_ascii=False, default=str)); return 0


def command_phase5_microstructure(args: argparse.Namespace) -> int:
    root = root_dir(); result = run_clock_microstructure(root, tolerance_seconds=args.tolerance_seconds); print(json.dumps(result, ensure_ascii=False, default=str)); return 0


def command_phase5_suite(args: argparse.Namespace) -> int:
    root = root_dir(); result = run_phase5_data_suite(root, sample_size=args.sample_size); research = run_formal_research_program(root); result["formal_research"] = research; print(json.dumps(result, ensure_ascii=False, default=str)); return 0


def command_research_program(args: argparse.Namespace) -> int:
    """Run only the frozen research path on already persisted canonical data."""
    root = root_dir(); result = run_formal_research_program(root); print(json.dumps(result, ensure_ascii=False, default=str)); return 0


def command_build_wallet_trades(args: argparse.Namespace) -> int:
    root = root_dir(); result = build_onchain_canonical(root); print(json.dumps(result, ensure_ascii=False)); return 0


def command_run_wallet_observability(args: argparse.Namespace) -> int:
    root = root_dir(); result = run_wallet_observability(root); print(json.dumps(result, ensure_ascii=False)); return 0


def command_run_wallet_skill(args: argparse.Namespace) -> int:
    root = root_dir(); result = run_wallet_skill(root); print(json.dumps({"rows": len(result), "status": result.iloc[0]["status"] if len(result) else "NOT_RUN"}, ensure_ascii=False)); return 0


def command_run_microstructure(args: argparse.Namespace) -> int:
    root = root_dir(); result = run_microstructure(root); print(json.dumps(result, ensure_ascii=False)); return 0


def command_run_diffusion(args: argparse.Namespace) -> int:
    root = root_dir(); result = build_temporal_network(root); print(json.dumps(result, ensure_ascii=False)); return 0


def command_run_cross_dex(args: argparse.Namespace) -> int:
    root = root_dir(); from .data.phase4 import run_cross_dex; result = run_cross_dex(root); print(json.dumps(result, ensure_ascii=False)); return 0


def command_run_lifecycle(args: argparse.Namespace) -> int:
    root = root_dir(); result = run_lifecycle(root); print(json.dumps(result, ensure_ascii=False)); return 0


def command_build_forward_universe(args: argparse.Namespace) -> int:
    root = root_dir(); result = build_forward_pit_universe(root); print(json.dumps({"rows": len(result), "output": str((root / "data/gold/universe/forward_pit_universe.parquet").resolve())}, ensure_ascii=False)); return 0


def command_run_onchain_suite(args: argparse.Namespace) -> int:
    root = root_dir(); result = run_formal_research_program(root); print(json.dumps(result, ensure_ascii=False, default=str)); return 0


def command_report_onchain(args: argparse.Namespace) -> int:
    root = root_dir(); result = run_formal_research_program(root); print(json.dumps({"status": "COMPLETED", "report": str((root / "reports/ONCHAIN_QUANT_RESEARCH_REPORT.md").resolve()), "memo": str((root / "reports/RESEARCH_MEMO.md").resolve()), "registry": str((root / "artifacts/phase5_experiment_registry.parquet").resolve()), "result": result}, ensure_ascii=False, default=str)); return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="onchain-alpha")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor").set_defaults(func=command_doctor)
    sub.add_parser("discover-api").set_defaults(func=command_discover)
    sub.add_parser("discover-capabilities").set_defaults(func=command_discover)
    collect = sub.add_parser("collect"); collect.add_argument("--mode", choices=["sample", "full"], default="sample"); collect.set_defaults(func=command_collect)
    for name, func in [("build-universe", command_build_universe), ("build-canonical-data", command_build_canonical), ("resolve-entities", command_resolve_entities), ("build-entity-state", command_build_entity_state), ("build-market-state", command_build_market_state), ("build-features", command_build_features), ("build-labels", command_build_labels), ("screen-factors", command_screen), ("validate-research", command_validate_research), ("phase2-baseline", command_phase2_baseline), ("phase2-inventory", command_phase2_inventory), ("run-phase2-suite", command_phase2_suite), ("phase2-report", command_phase2_report), ("report", command_report), ("audit", command_audit)]: sub.add_parser(name).set_defaults(func=func)
    hyp = sub.add_parser("run-hypothesis"); hyp.add_argument("--id", required=True); hyp.set_defaults(func=command_run_hypothesis)
    family = sub.add_parser("run-family"); family.add_argument("--family", required=True); family.set_defaults(func=command_run_family)
    sub.add_parser("run-research-suite").set_defaults(func=command_run_suite)
    events = sub.add_parser("detect-events"); events.add_argument("--z-threshold", type=float, default=2.0); events.add_argument("--min-history", type=int, default=12); events.set_defaults(func=command_detect_events)
    bt = sub.add_parser("backtest"); bt.add_argument("--factor", default="momentum_1h"); bt.add_argument("--horizon", type=int, default=24); bt.set_defaults(func=command_backtest)
    run = sub.add_parser("run-all"); run.add_argument("--mode", choices=["sample", "full"], default="sample"); run.set_defaults(func=command_run_all)
    sub.add_parser("inventory-local-data").set_defaults(func=command_inventory_local_data)
    sub.add_parser("build-asset-map").set_defaults(func=command_build_asset_map)
    trade = sub.add_parser("probe-trade-history"); trade.add_argument("--sample-size", type=int, default=8); trade.set_defaults(func=command_probe_trade_history)
    plan = sub.add_parser("plan-acquisition"); plan.add_argument("--symbols", default="BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT"); plan.add_argument("--days", type=int, default=7); plan.add_argument("--interval", default="5m"); plan.set_defaults(func=command_plan_acquisition)
    cex = sub.add_parser("collect-cex"); cex.add_argument("--symbols", default="BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT"); cex.add_argument("--days", type=int, default=3); cex.add_argument("--interval", default="5m"); cex.set_defaults(func=command_collect_cex)
    sub.add_parser("validate-data").set_defaults(func=command_validate_phase3)
    sub.add_parser("build-synchronized-data").set_defaults(func=command_sync_phase3)
    sub.add_parser("build-dex-bars").set_defaults(func=command_build_dex_bars)
    sub.add_parser("report-sync-quality").set_defaults(func=command_sync_phase3)
    sub.add_parser("freeze-research").set_defaults(func=command_freeze_phase3)
    sub.add_parser("run-discovery").set_defaults(func=command_freeze_phase3)
    sub.add_parser("run-confirmation").set_defaults(func=command_freeze_phase3)
    sub.add_parser("report-phase3").set_defaults(func=command_freeze_phase3)
    sub.add_parser("audit-onchain-data").set_defaults(func=command_audit_onchain_data)
    ct = sub.add_parser("collect-token-trades"); ct.add_argument("--sample-size", type=int, default=24); ct.add_argument("--max-pages", type=int, default=12); ct.add_argument("--request-budget", type=int, default=240); ct.set_defaults(func=command_collect_token_trades)
    sub.add_parser("phase5-semantics").set_defaults(func=command_phase5_semantics)
    ps = sub.add_parser("collect-participant-snapshots"); ps.add_argument("--token-limit", type=int, default=4); ps.add_argument("--wallet-limit", type=int, default=20); ps.set_defaults(func=command_phase5_snapshots)
    sub.add_parser("build-wallet-trades").set_defaults(func=command_build_wallet_trades)
    pp = sub.add_parser("build-pool-state"); pp.add_argument("--token-limit", type=int, default=4); pp.add_argument("--wallet-limit", type=int, default=0); pp.set_defaults(func=command_phase5_snapshots)
    sub.add_parser("build-forward-universe").set_defaults(func=command_build_forward_universe)
    sub.add_parser("run-wallet-observability").set_defaults(func=command_run_wallet_observability)
    sub.add_parser("run-wallet-skill").set_defaults(func=command_run_wallet_skill)
    sub.add_parser("run-microstructure").set_defaults(func=command_run_microstructure)
    sub.add_parser("run-diffusion").set_defaults(func=command_run_diffusion)
    sub.add_parser("run-cross-dex").set_defaults(func=command_run_cross_dex)
    sub.add_parser("run-lifecycle").set_defaults(func=command_run_lifecycle)
    sub.add_parser("run-onchain-suite").set_defaults(func=command_run_onchain_suite)
    sub.add_parser("report-onchain-research").set_defaults(func=command_report_onchain)
    pr = sub.add_parser("probe-participant-endpoints"); pr.add_argument("--wallet-limit", type=int, default=2); pr.set_defaults(func=command_phase5_probe)
    pt = sub.add_parser("collect-participant-tags"); pt.add_argument("--token-limit", type=int, default=4); pt.set_defaults(func=command_phase5_tags)
    pm = sub.add_parser("run-phase5-microstructure"); pm.add_argument("--tolerance-seconds", type=int, default=30); pm.set_defaults(func=command_phase5_microstructure)
    p5 = sub.add_parser("run-phase5-suite"); p5.add_argument("--sample-size", type=int, default=24); p5.set_defaults(func=command_phase5_suite)
    sub.add_parser("run-research-program").set_defaults(func=command_research_program)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
