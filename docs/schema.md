# Schema

## Point-in-time observation

Every normalized row aims to include `source`, `endpoint`, `chain`, `entity_type`, `token_address`, `wallet_address`, `event_time`, `observed_at`, `effective_time`, `ingested_at`, `api_version`, `request_params`, `request_params_hash`, `payload_hash`, `known_at`, `is_feature_safe`, and `leakage_reason`.

## Silver tables

- `market_observations`: token snapshots and candles with price, volume, liquidity, holders, transaction counts, and buy/sell fields.
- `universe`: token discovery snapshots with first/last seen and discovery source.
- `factor_panel`: point-in-time factor values keyed by token and observation time.
- `labels`: forward returns with explicit feature/entry/exit timestamps.

## Gold artifacts

Parquet is the primary research format. DuckDB is a local catalog/query engine and does not require all data to be imported.
