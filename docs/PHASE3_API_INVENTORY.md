# Phase III API inventory

Only read-only endpoints are listed. Web3 capabilities without a documented path are marked NOT_PROBED; no guessed URL was called.

| Product | Capability | Endpoint | Documentation | Probe |
|---|---|---|---|---|
| <bound method Series.prod of product                                                       Binance CEX
capability                                                    spot_klines
endpoint                                                   /api/v3/klines
method                                                                GET
documentation_status                                           DOCUMENTED
probe_status                                  ACCESSIBLE_WITH_CURRENT_KEY
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   Successful raw response exists; this run reuse...
Name: 0, dtype: object> | spot_klines | `/api/v3/klines` | DOCUMENTED | ACCESSIBLE_WITH_CURRENT_KEY |
| <bound method Series.prod of product                                                       Binance CEX
capability                                                      um_klines
endpoint                                                  /fapi/v1/klines
method                                                                GET
documentation_status                                           DOCUMENTED
probe_status                                  ACCESSIBLE_WITH_CURRENT_KEY
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   Successful raw response exists; this run reuse...
Name: 1, dtype: object> | um_klines | `/fapi/v1/klines` | DOCUMENTED | ACCESSIBLE_WITH_CURRENT_KEY |
| <bound method Series.prod of product                                                       Binance CEX
capability                                                 um_mark_klines
endpoint                                         /fapi/v1/markPriceKlines
method                                                                GET
documentation_status                                           DOCUMENTED
probe_status                                  ACCESSIBLE_WITH_CURRENT_KEY
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   Successful raw response exists; this run reuse...
Name: 2, dtype: object> | um_mark_klines | `/fapi/v1/markPriceKlines` | DOCUMENTED | ACCESSIBLE_WITH_CURRENT_KEY |
| <bound method Series.prod of product                                                       Binance CEX
capability                                                um_index_klines
endpoint                                        /fapi/v1/indexPriceKlines
method                                                                GET
documentation_status                                           DOCUMENTED
probe_status                                                FAILED_PARAMS
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   Endpoint responded with HTTP 400 in the safe p...
Name: 3, dtype: object> | um_index_klines | `/fapi/v1/indexPriceKlines` | DOCUMENTED | FAILED_PARAMS |
| <bound method Series.prod of product                                                       Binance CEX
capability                                              um_premium_klines
endpoint                                      /fapi/v1/premiumIndexKlines
method                                                                GET
documentation_status                                           DOCUMENTED
probe_status                                  ACCESSIBLE_WITH_CURRENT_KEY
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   Successful raw response exists; this run reuse...
Name: 4, dtype: object> | um_premium_klines | `/fapi/v1/premiumIndexKlines` | DOCUMENTED | ACCESSIBLE_WITH_CURRENT_KEY |
| <bound method Series.prod of product                                                       Binance CEX
capability                                                     um_funding
endpoint                                             /fapi/v1/fundingRate
method                                                                GET
documentation_status                                           DOCUMENTED
probe_status                                  ACCESSIBLE_WITH_CURRENT_KEY
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   Successful raw response exists; this run reuse...
Name: 5, dtype: object> | um_funding | `/fapi/v1/fundingRate` | DOCUMENTED | ACCESSIBLE_WITH_CURRENT_KEY |
| <bound method Series.prod of product                                                       Binance CEX
capability                                                     um_oi_hist
endpoint                                   /futures/data/openInterestHist
method                                                                GET
documentation_status                                           DOCUMENTED
probe_status                                                FAILED_PARAMS
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   Endpoint responded with HTTP 400 in the safe p...
Name: 6, dtype: object> | um_oi_hist | `/futures/data/openInterestHist` | DOCUMENTED | FAILED_PARAMS |
| <bound method Series.prod of product                                                      Binance Web3
capability                                                holders ranking
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 7, dtype: object> | holders ranking | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                                    top traders
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 8, dtype: object> | top traders | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                                   token trades
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 9, dtype: object> | token trades | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                     address portfolio overview
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 10, dtype: object> | address portfolio overview | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                             address recent PnL
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 11, dtype: object> | address recent PnL | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                              address token PnL
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 12, dtype: object> | address token PnL | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                      address DEX trade history
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 13, dtype: object> | address DEX trade history | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                                    leaderboard
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 14, dtype: object> | leaderboard | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                                 tracked trades
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 15, dtype: object> | tracked trades | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                               address balances
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 16, dtype: object> | address balances | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
| <bound method Series.prod of product                                                      Binance Web3
capability                                        transactions by address
endpoint                                                                 
method                                                                   
documentation_status                 NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG
probe_status                                                   NOT_PROBED
source                     https://developers.binance.com/en/docs/catalog
read_only                                                            True
notes                   The official public catalog exposes product fa...
Name: 17, dtype: object> | transactions by address | `` | NOT_FOUND_IN_OFFICIAL_PUBLIC_CATALOG | NOT_PROBED |
