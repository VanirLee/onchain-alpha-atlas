# Binance Web3 API capabilities

Generated at `2026-09-16T13:32:28.476567+00:00`. All probes were read-only.

Official catalog reference: https://developers.binance.com/en/docs/catalog

| Endpoint | Method | Status | HTTP/code | Fields | Latency ms |
|---|---:|---|---|---|---:|
| `/api/v1/dex/market/token/hot-token` | GET | supported | 200/0 | `items, page` | 3945.9 |
| `/api/v1/dex/market/token/hot-token` | GET | supported | 200/0 | `items, page` | 1130.9 |
| `/api/v1/dex/market/token/hot-token` | GET | supported | 200/0 | `items, page` | 488.2 |
| `/api/v1/dex/market/token/hot-token` | GET | supported | 200/0 | `items, page` | 486.0 |
| `/api/v1/dex/market/price-info` | POST | supported | 200/0 | `binanceChainId, bnBuyTxs1H, bnBuyTxs24H, bnBuyTxs4H, bnBuyTxs5M, bnBuyVolume1H, bnBuyVolume24H, bnBuyVolume4H, bnBuyVolume5M, bnSellTxs1H, bnSellTxs24H, bnSellTxs4H, bnSellTxs5M, bnSellVolume1H, bnSellVolume24H, bnSellVolume4H, bnSellVolume5M, bnTxs1H, bnTxs24H, bnTxs4H, bnTxs5M, bnVolume1H, bnVolume24H, bnVolume4H, bnVolume5M, buyTxs1H, buyTxs24H, buyTxs4H, buyTxs5M, buyVolume1H, buyVolume24H, buyVolume4H, buyVolume5M, circSupply, holders, liquidity, marketCap, maxPrice, minPrice, price, priceChange1H, priceChange24H, priceChange4H, priceChange5M, sellTxs1H, sellTxs24H, sellTxs4H, sellTxs5M, sellVolume1H, sellVolume24H, sellVolume4H, sellVolume5M, time, tokenContractAddress, txs1H, txs24H, txs4H, txs5M, volume1H, volume24H, volume4H, volume5M` | 426.3 |
| `/api/v1/dex/market/candles` | GET | supported | 200/0 | `open, high, low, close, volume, time, tx_count` | 1157.5 |
| `/api/v1/dex/market/token/advanced-info` | GET | supported | 200/0 | `binanceChainId, bnHolderCount, bnTraderCount7D, bundlerHoldingPercent, createTime, creatorAddress, devCreatedTokenCount, devHoldingPercent, devMigratedTokenCount, devMigratedTokenPercent, freshWalletHoldingPercent, holders, insiderHoldingPercent, isInternal, kolHoldingPercent, proHoldingPercent, progress, protocolId, smartMoneyHoldingPercent, sniperHoldingPercent, tokenContractAddress, tokenTags, top10HoldingPercent` | 1293.9 |
| `/api/v1/dex/market/token/top-liquidity` | GET | supported | 200/0 | `liquidityAmount, liquidityUsd, pool, poolAddress, protocolLogoUrl, protocolName` | 361.5 |
| `/api/v1/dex/market/trades` | GET | supported | 200/0 | `cursor, trades` | 393.2 |

## Read-only endpoint inventory

Status values: `DOCUMENTED`, `ACCESSIBLE_WITH_CURRENT_KEY`, `FAILED_PERMISSION`, `FAILED_PARAMS`, `NOT_PROBED`. The requested wallet analytics capabilities without an official public path are recorded as `NOT_PROBED`; no guessed URL was called.

| Capability | Candidate endpoint | Documentation | Probe status | HTTP/code | Reason |
|---|---|---|---|---|---|
| /api/v1/dex/market/token/hot-token | `/api/v1/dex/market/token/hot-token` | PROJECT_API_CONTRACT | ACCESSIBLE_WITH_CURRENT_KEY | 200/0 | Safe read-only probe using current key and documented project API contract. |
| /api/v1/dex/market/token/hot-token | `/api/v1/dex/market/token/hot-token` | PROJECT_API_CONTRACT | ACCESSIBLE_WITH_CURRENT_KEY | 200/0 | Safe read-only probe using current key and documented project API contract. |
| /api/v1/dex/market/token/hot-token | `/api/v1/dex/market/token/hot-token` | PROJECT_API_CONTRACT | ACCESSIBLE_WITH_CURRENT_KEY | 200/0 | Safe read-only probe using current key and documented project API contract. |
| /api/v1/dex/market/token/hot-token | `/api/v1/dex/market/token/hot-token` | PROJECT_API_CONTRACT | ACCESSIBLE_WITH_CURRENT_KEY | 200/0 | Safe read-only probe using current key and documented project API contract. |
| /api/v1/dex/market/price-info | `/api/v1/dex/market/price-info` | PROJECT_API_CONTRACT | ACCESSIBLE_WITH_CURRENT_KEY | 200/0 | Safe read-only probe using current key and documented project API contract. |
| /api/v1/dex/market/candles | `/api/v1/dex/market/candles` | PROJECT_API_CONTRACT | ACCESSIBLE_WITH_CURRENT_KEY | 200/0 | Safe read-only probe using current key and documented project API contract. |
| /api/v1/dex/market/token/advanced-info | `/api/v1/dex/market/token/advanced-info` | PROJECT_API_CONTRACT | ACCESSIBLE_WITH_CURRENT_KEY | 200/0 | Safe read-only probe using current key and documented project API contract. |
| /api/v1/dex/market/token/top-liquidity | `/api/v1/dex/market/token/top-liquidity` | PROJECT_API_CONTRACT | ACCESSIBLE_WITH_CURRENT_KEY | 200/0 | Safe read-only probe using current key and documented project API contract. |
| /api/v1/dex/market/trades | `/api/v1/dex/market/trades` | PROJECT_API_CONTRACT | ACCESSIBLE_WITH_CURRENT_KEY | 200/0 | Safe read-only probe using current key and documented project API contract. |
| holders ranking | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| top traders | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| token trades | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| address portfolio overview | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| address recent PnL | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| address token PnL | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| address DEX trade history | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| leaderboard | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| tracked trades | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| address balances | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |
| transactions by address | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED | / | The official public catalog exposes product families but no Web3 analytics path for this capability; no speculative endpoint was called. |

## Confirmed or observed capabilities

{
  "market": [
    "/api/v1/dex/market/price-info",
    "/api/v1/dex/market/candles"
  ],
  "liquidity": [
    "/api/v1/dex/market/token/top-liquidity"
  ],
  "holder": [
    "/api/v1/dex/market/token/advanced-info: holders, bnHolderCount, top10HoldingPercent, freshWalletHoldingPercent, insiderHoldingPercent"
  ],
  "wallet": [
    "unknown: no project hint or safe probe"
  ],
  "ranking": [
    "/api/v1/dex/market/token/hot-token"
  ],
  "smart_money": [
    "/api/v1/dex/market/token/advanced-info: smartMoneyHoldingPercent (crowding/holding proxy only; no forward signal outcome confirmed)"
  ],
  "audit": [
    "/api/v1/dex/market/token/advanced-info"
  ],
  "event_meme": [
    "unknown: no event/meme lifecycle endpoint confirmed"
  ],
  "ohlcv_intervals": [
    "1h probe attempted"
  ]
}

## Rate-limit observations

{
  "requests": 9,
  "success": 9,
  "errors": 0,
  "429": 0,
  "5xx": 0,
  "latencies_ms": [
    3945.9421660285443,
    1130.9010419645347,
    488.21645899442956,
    485.9896249836311,
    426.2750410125591,
    1157.5252499897033,
    1293.8957079895772,
    361.4578749984503,
    393.2265829644166
  ],
  "rate_limit_headers": [
    {
      "x-oc-ratelimit-limit": "3000",
      "x-oc-ratelimit-remaining": "2999",
      "x-oc-used-weight": "1"
    },
    {
      "x-oc-ratelimit-limit": "3000",
      "x-oc-ratelimit-remaining": "2999",
      "x-oc-used-weight": "1"
    },
    {
      "x-oc-ratelimit-limit": "3000",
      "x-oc-ratelimit-remaining": "2998",
      "x-oc-used-weight": "2"
    },
    {
      "x-oc-ratelimit-limit": "3000",
      "x-oc-ratelimit-remaining": "2998",
      "x-oc-used-weight": "2"
    },
    {
      "x-oc-ratelimit-limit": "3000",
      "x-oc-ratelimit-remaining": "2999",
      "x-oc-used-weight": "1"
    },
    {
      "x-oc-ratelimit-limit": "3000",
      "x-oc-ratelimit-remaining": "2999",
      "x-oc-used-weight": "1"
    },
    {
      "x-oc-ratelimit-limit": "3000",
      "x-oc-ratelimit-remaining": "2999",
      "x-oc-used-weight": "1"
    },
    {
      "x-oc-ratelimit-limit": "3000",
      "x-oc-ratelimit-remaining": "2999",
      "x-oc-used-weight": "1"
    },
    {
      "x-oc-ratelimit-limit": "3000",
      "x-oc-ratelimit-remaining": "2999",
      "x-oc-used-weight": "1"
    }
  ]
}

Unknown wallet holdings, signal-outcome, and event/meme lifecycle endpoints are intentionally left as adapter extension points. Holder fields and the smart-money holding/crowding proxy were observed through `advanced-info`; no forward signal-outcome endpoint was confirmed. No unsupported endpoint was invented.
