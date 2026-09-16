# Canonical data model

The canonical Parquet layer currently writes:

- `dim_asset`: asset identity, chain/address, source, observed lifetime, and
  optional canonical cross-chain identity.
- `fact_token_market_state`: price, volume, liquidity, market cap, holders,
  buy/sell, and PIT clocks.
- `events`: standard event schema with detector version and metadata.
- `outcomes`: future timestamp-aligned returns and market responses as the
  research suite expands.
- `experiment_registry`: hypothesis, variant, dataset/code/config lineage,
  result and OOS status.

Future schemas reserve `dim_wallet`, `fact_dex_trade`, `fact_wallet_state`,
`fact_cex_state`, `temporal_graph_edges`, and `outcomes`. Missing real sources
produce `BLOCKED_BY_DATA`, not synthetic rows.
