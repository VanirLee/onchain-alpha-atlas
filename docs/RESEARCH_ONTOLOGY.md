# Research ontology

## Entities

`wallet`, `entity`, `token`, `pool`, `dex`, `chain`, `bridge`, `cex`,
`cex_instrument`, `transaction`, `trade`, `market_event`.

## Economic primitives

`information`, `flow`, `inventory`, `liquidity`, `crowding`, `relative_value`,
`volatility_risk`, `regime_state`, `diffusion`, `execution`.

Every hypothesis declares at least one primitive. `asset_id` is
`chain:lower(token_address)`. `canonical_asset_id` is only populated when a
cross-chain identity mapping is verified; symbols are never identity keys.

## Four clocks

Every event/state observation carries `event_time`, `observed_time`,
`available_time`, and `ingest_time`. A feature may be used at decision time d
only when `available_time <= d`.
