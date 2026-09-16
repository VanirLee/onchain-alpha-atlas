# Phase II Data Expansion Plan

## Budget decision

The current saved panel already satisfies the Stage B pilot size (112 assets, 4 chains, 10,079 token-market observations). A new full-universe download is therefore deferred until the missing research dimensions justify the request budget. The current Phase II run uses the saved real Web3 panel and performs no speculative wallet or CEX requests.

| Stage | Scope | Estimated requests | Expected value | Gate |
|---|---|---:|---|---|
| A validation | 5–20 assets, 2–4 chains, 1h candles + market snapshots | 30–120 | validate schema, pagination, clocks, dedup | PASS already recorded |
| B research pilot | 50–150 assets, 4 chains, 1h history plus event/state features | 120–2,000 | event, lead-lag, OOS pilot | current saved 112-asset panel |
| C broad dataset | 100–500+ assets, longer history, venue/entity enrichment | 2,000–20,000+ | cross-chain and state robustness | requires fresh capability and rate-budget approval |

## Priority acquisition order

1. Binance Spot public klines/trades/depth for symbols that can be mapped to the Web3 asset universe.
2. USDⓈ-M Futures klines, funding, OI history, mark/index/premium data for price-discovery and state dependence.
3. Web3 token-trade pagination with wallet/address fields, then wallet balances/holdings and closed-trade outcomes.

The client target remains 40 QPS or below the configured ceiling, with endpoint-specific weights, checkpoints, content-addressed Bronze cache, retry/backoff, and safe restart. No write endpoint is in scope.

## Stop conditions

- Stop if a new source does not materially increase independent event episodes, historical depth, entity coverage, or venue coverage.
- Do not scale Stage C using the current hot-token ranking as if it were a PIT historical universe.
- Do not call undocumented wallet endpoints or infer CEX permission from a Web3 key.
