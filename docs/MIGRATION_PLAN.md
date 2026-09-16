# Research Paradigm Migration Plan

Generated after a full repository scan on 2026-09-16. The project is being
migrated from a factor-centric token panel into an on-chain information
discovery and transmission research platform.

## A. Reuse unchanged

- `src/onchain_alpha/connectors/binance_web3.py`: signed read-only allowlist,
  rate limiter, endpoint semaphore, retry/backoff, safe headers.
- `src/onchain_alpha/storage/`: Bronze/Silver/Gold stores, hashes,
  checkpoints, and DuckDB catalog.
- `src/onchain_alpha/features/core.py` and
  `src/onchain_alpha/labels/forward_returns.py`: corrected timestamp-aware PIT
  baseline; factor work becomes a baseline rather than the research interface.
- `src/onchain_alpha/screening/ic.py` and
  `src/onchain_alpha/stats/multiple_testing.py`: corrected IC inference,
  HAC, and BH-FDR.
- `src/onchain_alpha/stats/robustness.py` and
  `src/onchain_alpha/backtest/engine.py`: purged OOS and non-overlapping
  baseline accounting.
- Existing real Bronze/Silver/Gold data, API capability evidence, tests, and
  secret-safe audit workflow.

## B. Refactor

- CLI now exposes research-family commands while preserving existing commands.
- Factor results are explicitly labelled as `FAMILY_BASELINE` and are not a
  required input to event, entity, lead-lag, graph, or state research.
- Pipeline manifests gain ontology, hypothesis, experiment, dataset, and code
  lineage fields.
- Research reports are organized by family, with baseline factor output kept as
  one section.

## C. Downgrade to baseline

- The existing 30-factor engine, rank IC, quantile analysis, and long-only
  portfolio are retained as diagnostic baselines.
- Current hot-token discovery remains `CURRENT-UNIVERSE-BACKFILL`; it must not
  be described as a historical point-in-time universe.

## D. Add

- Canonical ontology and four-clock PIT schema: event, observed, available,
  ingest time.
- Asset, wallet/entity, trade, market-state, event, outcome, and experiment
  registry schemas.
- YAML hypothesis registry with classification and research gates.
- Generic event detector/event-study engine with overlap diagnostics and
  bootstrap intervals.
- Wallet skill engine that uses only closed trades before measurement time and
  returns `BLOCKED_BY_DATA` when wallet trades are unavailable.
- Generic lead-lag engine using timestamp-aligned series, distributed lags,
  HAC inference, and non-causal interpretation.
- Temporal graph as-of snapshots; current data lack a real trade-edge panel, so
  graph research is schema-ready but data-blocked.
- Machine-readable family outputs and formal lineage.

## E. Historical results that cannot be reused as evidence

- Any pre-migration factor p-value based on averaged cross-sectional p-values.
- Any result built from row-position horizons rather than exact timestamps.
- Any overlapping-forward-return cumprod backtest.
- Any wallet/entity label based on full-sample future PnL.
- Any result in which a current hot-token ranking is described as a historical
  all-token universe.

## F. Data that can be reused

- Real Binance Web3 token discovery, price-info, 1h candle observations,
  holder/crowding proxy fields, and raw payload hashes.
- Existing factor/label artifacts only after rebuilding them with the corrected
  source code.
- Existing API capability and rate-limit observations.

## G. Verified capabilities

- Four chains: Ethereum `1`, BSC `56`, Base `8453`, Solana `CT_501`.
- Read-only hot-token discovery, batch price-info, 1h candles, advanced-info,
  top-liquidity probe, and trades capability probe.
- No verified wallet holdings, wallet PnL, leaderboard, address portfolio, or
  event/meme lifecycle endpoint in the current public catalog/key scope.

## H. Data-blocked research

- Wallet/entity skill: `BLOCKED_BY_DATA`; no wallet trade history is in the
  current real dataset.
- Full information transmission chain wallet → DEX → CEX → perpetual →
  funding/OI: `BLOCKED_BY_DATA`; no CEX/derivatives or wallet stream is present.
- Temporal graph diffusion: schema and as-of engine are implemented, but real
  trade-edge results are `BLOCKED_BY_DATA`.
- Executable capacity and arbitrage: no executable depth, quotes, gas, latency,
  or venue access panel is present.

## Migration order

1. Ontology/canonical schema and hypothesis/experiment registry.
2. Generic event study and real H001 volume-shock event study.
3. Wallet skill blocked-safe implementation and adversarial PIT test.
4. Lead-lag engine and real H002 market volume/return lead-lag study.
5. Factor engine reclassified as baseline; existing corrected tests retained.
6. Research gates, falsification records, family outputs, report, and audit.

The implementation intentionally stops short of fabricating wallet, CEX, or
graph evidence. Missing capabilities are explicit machine-readable statuses.
