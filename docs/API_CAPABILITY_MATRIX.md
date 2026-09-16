# API Capability Matrix

Generated from the fresh read-only Web3 capability report plus official Binance market-data documentation. No speculative endpoint was called.

Status values: `ACCESSIBLE`, `DOCUMENTED_NOT_PROBED`, `PERMISSION_DENIED`, `INVALID_TEST_PARAMS`, `UNSUPPORTED`, `DEPRECATED`, `UNKNOWN`.

| source | api_family | endpoint | method | entity_type | data_type | historical_or_snapshot | current_key_access | probe_status | research_value |
|---|---|---|---|---|---|---|---|---|---|
| Binance Web3 | Web3 DEX market | /api/v1/dex/market/token/hot-token | GET | token | market/flow/ranking | snapshot | True | ACCESSIBLE | liquidity/holder proxy enrichment |
| Binance Web3 | Web3 DEX market | /api/v1/dex/market/token/hot-token | GET | token | market/flow/ranking | snapshot | True | ACCESSIBLE | liquidity/holder proxy enrichment |
| Binance Web3 | Web3 DEX market | /api/v1/dex/market/token/hot-token | GET | token | market/flow/ranking | snapshot | True | ACCESSIBLE | liquidity/holder proxy enrichment |
| Binance Web3 | Web3 DEX market | /api/v1/dex/market/token/hot-token | GET | token | market/flow/ranking | snapshot | True | ACCESSIBLE | liquidity/holder proxy enrichment |
| Binance Web3 | Web3 DEX market | /api/v1/dex/market/price-info | POST | token | market/flow/ranking | snapshot | True | ACCESSIBLE | market backbone, event detection, lead-lag, state conditioning |
| Binance Web3 | Web3 DEX market | /api/v1/dex/market/candles | GET | token | market/flow/ranking | historical | True | ACCESSIBLE | market backbone, event detection, lead-lag, state conditioning |
| Binance Web3 | Web3 DEX market | /api/v1/dex/market/token/advanced-info | GET | token | market/flow/ranking | snapshot | True | ACCESSIBLE | liquidity/holder proxy enrichment |
| Binance Web3 | Web3 DEX market | /api/v1/dex/market/token/top-liquidity | GET | token | market/flow/ranking | snapshot | True | ACCESSIBLE | liquidity/holder proxy enrichment |
| Binance Web3 | Web3 DEX market | /api/v1/dex/market/trades | GET | token | market/flow/ranking | snapshot | True | ACCESSIBLE | liquidity/holder proxy enrichment |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | holders ranking | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | top traders | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | token trades | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | address portfolio overview | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | address recent PnL | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | address token PnL | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | address DEX trade history | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | leaderboard | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | tracked trades | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | address balances | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance Web3 | Web3 analytics |  |  | wallet/entity | transactions by address | unknown | unknown | DOCUMENTED_NOT_PROBED | wallet/entity/network research |
| Binance official docs | Spot | https://data-api.binance.vision/api/v3/klines | GET | instrument | OHLCV | historical | unknown | DOCUMENTED_NOT_PROBED | historical market backbone |
| Binance official docs | Spot | https://data-api.binance.vision/api/v3/aggTrades | GET | instrument | aggregate trades | historical | unknown | DOCUMENTED_NOT_PROBED | historical market backbone / flow |
| Binance official docs | Spot | https://data-api.binance.vision/api/v3/depth | GET | instrument | order book | historical | unknown | DOCUMENTED_NOT_PROBED | market structure / execution |
| Binance official docs | USDⓈ-M Futures | https://fapi.binance.com/fapi/v1/klines | GET | instrument | OHLCV | historical | unknown | DOCUMENTED_NOT_PROBED | perpetual market backbone |
| Binance official docs | USDⓈ-M Futures | https://fapi.binance.com/fapi/v1/fundingRate | GET | instrument | funding | historical | unknown | DOCUMENTED_NOT_PROBED | state dependence / relative value |
| Binance official docs | USDⓈ-M Futures | https://fapi.binance.com/futures/data/openInterestHist | GET | instrument | open interest | historical | unknown | DOCUMENTED_NOT_PROBED | state dependence / crowding |
| Binance official docs | USDⓈ-M Futures | https://fapi.binance.com/fapi/v1/premiumIndex | GET | instrument | mark/index/funding snapshot | historical | unknown | DOCUMENTED_NOT_PROBED | price discovery / relative value |
| Binance official docs | COIN-M Futures | https://dapi.binance.com/dapi/v1/fundingRate | GET | instrument | funding | historical | unknown | DOCUMENTED_NOT_PROBED | state dependence / relative value |
| Binance official docs | COIN-M Futures | https://dapi.binance.com/dapi/v1/premiumIndexKlines | GET | instrument | premium index candles | historical | unknown | DOCUMENTED_NOT_PROBED | price discovery / relative value |

## Interpretation

Web3 market/ranking endpoints were probed with the current key. Official Spot and Futures market-data endpoints are documented but intentionally not probed with the Web3 credential; no CEX permission is inferred. Wallet/entity capabilities remain `DOCUMENTED_NOT_PROBED`/`UNKNOWN` because no public endpoint was confirmed in the current Web3 catalog.
