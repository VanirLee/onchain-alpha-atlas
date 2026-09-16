# Onchain Alpha Atlas

Large-scale point-in-time cross-chain factor mining with Binance Web3 read-only data.

This is a research platform, not an execution system. The current architecture is an information-discovery and transmission platform: event response, lead-lag, entity skill, temporal network, market state, and relative-value families are first-class research paths; the original factor engine is retained as a baseline. The network adapter has an explicit read-only allowlist and never builds, signs, approves, broadcasts, transfers, or submits transactions. Secrets are loaded from environment variables or the existing local `../web3-arb-lab/.env`; they are never printed or persisted to reports.

## Quick start

```bash
cd onchain-alpha-atlas
uv venv --python 3.11
uv sync --extra dev
uv run python -m onchain_alpha.cli doctor
uv run python -m onchain_alpha.cli discover-capabilities
uv run python -m onchain_alpha.cli run-all --mode sample
uv run python -m onchain_alpha.cli build-canonical-data
uv run python -m onchain_alpha.cli run-research-suite
uv run python -m onchain_alpha.cli validate-research
uv run python -m onchain_alpha.cli report
uv run pytest
uv run streamlit run app/main.py
```

If `uv` is unavailable, use `python3.11 -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'`.

The sample run defaults to 120 discovered tokens across the configured chains, collects current price-info plus 1h candles where available, and writes Bronze/Silver/Gold artifacts. It is intentionally bounded. Use `--mode full` only after inspecting rate-limit and data-quality reports.

## Commands

```bash
python -m onchain_alpha.cli doctor
python -m onchain_alpha.cli discover-api
python -m onchain_alpha.cli discover-capabilities
python -m onchain_alpha.cli collect --mode sample
python -m onchain_alpha.cli build-universe
python -m onchain_alpha.cli build-canonical-data
python -m onchain_alpha.cli resolve-entities
python -m onchain_alpha.cli detect-events
python -m onchain_alpha.cli build-entity-state
python -m onchain_alpha.cli build-market-state
python -m onchain_alpha.cli build-features
python -m onchain_alpha.cli build-labels
python -m onchain_alpha.cli screen-factors
python -m onchain_alpha.cli backtest
python -m onchain_alpha.cli run-hypothesis --id H001
python -m onchain_alpha.cli run-hypothesis --id H002
python -m onchain_alpha.cli run-hypothesis --id H003
python -m onchain_alpha.cli run-family --family event_response
python -m onchain_alpha.cli run-research-suite
python -m onchain_alpha.cli validate-research
python -m onchain_alpha.cli report
python -m onchain_alpha.cli audit
python -m onchain_alpha.cli run-all --mode sample
```

Phase II activation commands:

```bash
python -m onchain_alpha.cli phase2-baseline
python -m onchain_alpha.cli phase2-inventory
python -m onchain_alpha.cli run-phase2-suite
python -m onchain_alpha.cli phase2-report
```

These produce `data/API_CAPABILITY_MATRIX.parquet`, `artifacts/CEX_DATA_INVENTORY.csv`, `artifacts/research_coverage.parquet`, `artifacts/research_agenda.parquet`, `data/gold/canonical/universe_snapshot.parquet`, and the Phase II family outputs. The current saved dataset is a Stage B pilot; no speculative bulk download is performed until CEX/entity capability gates pass.

## Research paradigm and evidence status

The canonical model keeps four clocks (`event_time`, `observed_time`, `available_time`, `ingest_time`) and uses `(chain, token_address)` as the minimum asset identity. Hypotheses are YAML specifications under `configs/hypotheses/` and every attempted run is written to `artifacts/experiment_registry.parquet`.

The current real-data suite executes H001 volume-shock event response and H002 volume-to-future-return lead-lag on the saved Binance Web3 market panel. These are exploratory association studies, not causal claims. H003 wallet skill and the temporal network family return `BLOCKED_BY_DATA` until wallet trade/holding and entity-edge observations are actually available. See `docs/MIGRATION_PLAN.md`, `docs/RESEARCH_ONTOLOGY.md`, and `docs/RESEARCH_METHODOLOGY.md`.

Research outputs include `artifacts/event_study_results.parquet`, `artifacts/lead_lag_results.parquet`, `artifacts/wallet_skill_results.parquet`, `artifacts/network_results.parquet`, `artifacts/hypothesis_results.parquet`, and the formal factor/OOS/backtest artifacts. `BLOCKED_BY_DATA`, `INSUFFICIENT_EVIDENCE`, `EXPLORATORY`, and `SUPPORTED` are distinct states; an unsupported family is never silently replaced by a factor proxy.

## Evidence labels

Reports distinguish `real_api`, `local_reference`, `synthetic_test`, and `unsupported`. Short samples that do not support inference are reported as `insufficient evidence`, not as alpha.

## Phase III data-first backbone

The Phase III flow inventories local files before any download, reuses the existing AlphaLabOS 1h CEX panel read-only, and then runs a bounded public Binance CEX pilot:

```bash
python -m onchain_alpha.cli inventory-local-data
python -m onchain_alpha.cli plan-acquisition --days 3 --interval 5m
python -m onchain_alpha.cli probe-trade-history --sample-size 8
python -m onchain_alpha.cli collect-cex --days 3 --interval 5m
python -m onchain_alpha.cli build-dex-bars
python -m onchain_alpha.cli build-asset-map
python -m onchain_alpha.cli build-synchronized-data
python -m onchain_alpha.cli validate-data
python -m onchain_alpha.cli run-discovery
python -m onchain_alpha.cli report-phase3
```

Only public read-only market-data GET endpoints are used. Identity mapping never joins a Web3 token to a CEX instrument by symbol alone; the current run therefore reports zero verified DEX/CEX pairs and keeps R1–R4 blocked rather than fabricating cross-venue results. See `docs/LOCAL_DATA_CATALOG.md`, `docs/PHASE3_API_INVENTORY.md`, `docs/SYNC_QUALITY.md`, and `reports/PHASE3_RESEARCH_REPORT.md`.

## Phase V research-first on-chain program

The canonical formal path uses persisted Web3 trade data only; it does not call the superseded Phase IV suite and does not execute trades:

```bash
python -m onchain_alpha.cli audit-onchain-data
python -m onchain_alpha.cli collect-token-trades --sample-size 8
python -m onchain_alpha.cli build-wallet-trades
python -m onchain_alpha.cli build-forward-universe
python -m onchain_alpha.cli run-phase5-microstructure
python -m onchain_alpha.cli run-research-program
python -m onchain_alpha.cli report-onchain-research
```

The program registers RQ1–RQ12, runs R1–R4 response/size/flow/decay research, participant-label validation, wallet persistence, crowding observables, leave-one-token-out and early/late stability, then writes `reports/ONCHAIN_QUANT_RESEARCH_REPORT.md`, `reports/RESEARCH_MEMO.md`, `artifacts/RESEARCH_FREEZE.json`, and `artifacts/RESEARCH_SCORECARD.parquet`. Wallet skill, executable capacity, and any alpha claim remain gated by real data quality and forward confirmation.
