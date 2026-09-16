# Phase V on-chain capability and data semantics

Official Binance Web3 API inventory was checked against the current Web3 documentation. Only read-only endpoints are allowlisted in the client.

## Semantic contract

- `volume` is API USD trade amount and is stored as `usd_value`.
- `changedTokenInfo[queried token].amount` is stored as `token_quantity`.
- Other changedTokenInfo leg is stored as `paired_token_contract`, `paired_token_symbol`, `paired_token_quantity`.
- `type` is exact `buy`/`sell`; other values are `UNKNOWN` and trigger a schema diagnostic.
- No `volume * price` notional is used.

## Executed data expansion

- Historical depth: `{"tokens": 20, "pages": 111, "raw_trades": 9100, "dedup_trades": 9099, "output": "/Users/vanirli/Desktop/加密市场套利/onchain-alpha-atlas/artifacts/TOKEN_TRADE_HISTORY_DEPTH.parquet"}`
- Participant endpoint probes: `{"rows": 11, "accessible": 10}`
- Tag coverage rows: `28`
- Snapshot collection: `{"participant_snapshot_rows": 800, "pool_snapshot_rows": 4, "address_history_rows": 61, "address_transaction_rows": 20, "pool_count": 4}`

## Official endpoint reference

- Token trades: `/api/v1/dex/market/trades`, cursor/limit max 500, tagFilter documented.
- Holders/top traders: `/api/v1/dex/market/token/holder`, `/api/v1/dex/market/token/top-trader`.
- Top liquidity: `/api/v1/dex/market/token/top-liquidity`.
- Portfolio/history/leaderboard/tracked trades and wallet balances/transactions are probed and statused in `artifacts/PARTICIPANT_ENDPOINT_PROBES.parquet`.

External tag values are stored only as `external_label`; they are not estimated skill.
