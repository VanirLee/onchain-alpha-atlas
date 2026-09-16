# Price Semantics Audit

The API `price` is compared with `usd_value / abs(token_quantity)` and `paired_token_quantity / abs(token_quantity)`. The observed API field is pair-denominated; the USD-normalized implied price is therefore the research `P_event`.

- Canonical trades audited: **9299**
- Included by price validation gate: **9294**
- Excluded: **5**
- API-vs-paired consistency interval: **[0.1, 10.0]**
- External Binance token price/candle reference: **not available at the exact trade timestamps in the persisted sample; no false three-way agreement is claimed.**

## Exclusion reasons

- `API_PRICE_IS_PAIRED_DENOMINATED__USD_IMPLIED_PRICE_USED`: 9294 (99.95%)
- `API_PRICE_VS_PAIRED_PRICE_MISMATCH`: 2 (0.02%)
- `NON_POSITIVE_OR_NONFINITE_INPUT`: 3 (0.03%)

Per-asset quantiles and shares are in `artifacts/PRICE_SEMANTICS_BY_ASSET.parquet`. The 100 most extreme rows are in `artifacts/PRICE_SEMANTICS_EXTREMES.parquet`; raw payloads remain in the row-level `raw_json` field and are not silently discarded.
