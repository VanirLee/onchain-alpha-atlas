# Onchain Alpha Atlas

Point-in-time, cross-chain crypto research with Binance Web3 read-only data.

Onchain Alpha Atlas is a research platform for discovering how on-chain information is transmitted into market outcomes. It is **not** a trading bot, execution system, or wallet-management tool. The code uses read-only market/data access and does not build, sign, approve, broadcast, transfer, or submit transactions.

## What is in this repository?

The repository is organized as a browsable research project rather than a single opaque export:

| Area | Purpose |
| --- | --- |
| [`src/onchain_alpha/`](src/onchain_alpha/) | Python package: connectors, collectors, canonical data, features, labels, research, statistics, reporting, and CLI |
| [`configs/`](configs/) | Research agenda and hypothesis specifications H001–H007 |
| [`docs/`](docs/) | Architecture, data model, API capability matrix, PIT/leakage rules, limitations, and phase methodology |
| [`reports/`](reports/) | Human-readable research reports and CSV summaries |
| [`artifacts/`](artifacts/) | Run manifests, experiment registries, coverage tables, and result tables |
| [`tests/`](tests/) | Correctness and reproducibility tests |
| [`app/`](app/) | Streamlit research dashboard |
| [`scripts/`](scripts/) | Audit-bundle and reproducibility helpers |
| [`config/`](config/) | Safe example configuration templates |
| [`PROJECT_AUDIT_BUNDLE.zip`](PROJECT_AUDIT_BUNDLE.zip) | Frozen audit export; the browsable files above are preferred for inspection |

The public repository intentionally excludes API credentials, `.env` files, raw local caches, and large unreviewed data dumps. The audit bundle is retained as a snapshot, not as a substitute for the source tree.

## Research status

The project has moved from a generic factor prototype toward a research-first on-chain information backbone:

- **Canonical clocks:** `event_time`, `observed_time`, `available_time`, and `ingest_time`.
- **Minimum asset identity:** `(chain, token_address)`; symbol-only joins are not accepted.
- **Evidence labels:** `real_api`, `local_reference`, `synthetic_test`, and `unsupported`.
- **Honest result states:** `SUPPORTED`, `EXPLORATORY`, `INSUFFICIENT_EVIDENCE`, and `BLOCKED_BY_DATA`.
- **Research families:** event response, lead-lag, state dependence, participant/entity skill, temporal networks, market state, cross-venue discovery, and the baseline factor engine.

The saved run is a bounded pilot. It demonstrates the pipeline and its data-quality gates; it does not claim that every proposed factor or wallet-skill hypothesis is validated. Wallet skill, executable capacity, and cross-venue arbitrage remain gated until the required observations and executable quotes are available.

## Reproduce from a clean environment

Python 3.11+ is recommended. `uv` is preferred, but a standard virtual environment works too.

```bash
git clone https://github.com/VanirLee/onchain-alpha-atlas.git
cd onchain-alpha-atlas

# Preferred
uv venv --python 3.11
uv sync --extra dev

# Fallback
python3.11 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

The public repository contains templates only. Put private API settings in a local, ignored `.env` or settings file; never commit them.

Run the safe checks first:

```bash
uv run python -m onchain_alpha.cli doctor
uv run python -m onchain_alpha.cli discover-capabilities
uv run pytest
```

Run the bounded sample pipeline:

```bash
uv run python -m onchain_alpha.cli run-all --mode sample
uv run python -m onchain_alpha.cli build-canonical-data
uv run python -m onchain_alpha.cli run-research-suite
uv run python -m onchain_alpha.cli validate-research
uv run python -m onchain_alpha.cli report
```

Only after checking rate-limit and data-quality reports should a larger collection be considered:

```bash
uv run python -m onchain_alpha.cli run-all --mode full
```

## Main commands

```bash
# API and collection
python -m onchain_alpha.cli doctor
python -m onchain_alpha.cli discover-api
python -m onchain_alpha.cli discover-capabilities
python -m onchain_alpha.cli collect --mode sample

# Canonical data and PIT research
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

# Research and reporting
python -m onchain_alpha.cli run-research-suite
python -m onchain_alpha.cli validate-research
python -m onchain_alpha.cli report
python -m onchain_alpha.cli audit
```

For the Phase II–V research tracks, see [`docs/MIGRATION_PLAN.md`](docs/MIGRATION_PLAN.md), [`docs/RESEARCH_METHODOLOGY.md`](docs/RESEARCH_METHODOLOGY.md), and [`docs/ONCHAIN_DATA_CAPABILITY.md`](docs/ONCHAIN_DATA_CAPABILITY.md).

## Read the results

Start with:

1. [`reports/ONCHAIN_QUANT_RESEARCH_REPORT.md`](reports/ONCHAIN_QUANT_RESEARCH_REPORT.md) — research-first on-chain findings and blocked questions.
2. [`reports/ONCHAIN_RESEARCH_REPORT.md`](reports/ONCHAIN_RESEARCH_REPORT.md) — canonical on-chain research report.
3. [`reports/RESEARCH_MEMO.md`](reports/RESEARCH_MEMO.md) — concise research memo.
4. [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) — what the current data cannot support.
5. [`docs/API_CAPABILITY_MATRIX.md`](docs/API_CAPABILITY_MATRIX.md) and [`docs/api_capabilities.md`](docs/api_capabilities.md) — endpoint and data availability.
6. [`artifacts/RESEARCH_FREEZE.json`](artifacts/RESEARCH_FREEZE.json) and [`artifacts/experiment_registry.parquet`](artifacts/experiment_registry.parquet) — provenance and run registry.

CSV summaries in `reports/` are derived outputs. The code that produces them lives under `src/onchain_alpha/`; results should be regenerated rather than edited by hand.

## Dashboard

```bash
uv run streamlit run app/main.py
```

The dashboard exposes overview, data quality, research outputs, wallet/entity status, backtests, robustness checks, and event-study views when the corresponding artifacts are present.

## Safety and data boundaries

- Read-only data access is allowlisted in the connector layer.
- No order, transfer, signing, approval, or wallet mutation endpoint is used.
- Credentials are loaded only from local environment/configuration and are never printed to logs or reports.
- Raw Bronze/Silver/Gold data and local caches are excluded from the public repository.
- A missing observation is not silently replaced with a proxy observation.
- Short or biased samples are reported as `INSUFFICIENT_EVIDENCE`, not promoted to alpha.

## Project map

```text
onchain-alpha-atlas/
├── app/                 Streamlit dashboard
├── artifacts/           Run manifests, registries, and result tables
├── config/              Safe configuration templates
├── configs/             Hypotheses and research agenda
├── docs/                Methodology, schema, API, PIT, and limitations
├── reports/             Reports and tabular summaries
├── scripts/             Audit/reproducibility utilities
├── src/onchain_alpha/   Main Python package
└── tests/               Reproducibility and correctness tests
```

## License and research use

This repository is a research artifact. Results are exploratory unless a report explicitly provides sufficient coverage, out-of-sample support, and robustness evidence. Nothing here is financial advice or a promise of executable trading performance.
