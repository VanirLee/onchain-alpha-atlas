# Data → Research Map

This map distinguishes data availability from research claims. `CURRENT-UNIVERSE-BACKFILL` is not a historical listing universe.

| Data source | Key fields | Granularity | History | PIT risk | Research families | Main limitation |
|---|---|---|---|---|---|---|
| Web3 hot-token ranking | chain, token address, rank, symbol | token × discovery snapshot | current discovery | high if backfilled | universe discovery, event coverage | survivor/hot-token selection |
| Web3 price-info | price, volume windows, buy/sell volume, liquidity, market cap, holders | token × snapshot | snapshot | medium; available time must be retained | market backbone, flow, liquidity, state | not executable quote; sparse history |
| Web3 candles | OHLCV, time, trade count | token × 1h candle | API-returned historical depth | medium | event, lead-lag, factor baseline, state | 112-asset current universe; gaps and selection bias |
| Web3 advanced-info | holder count, top-10 concentration, smart-money holding proxy, creator fields | token × snapshot | snapshot | high for historical use | holder/crowding/risk proxies | no verified wallet identity or forward signal outcome |
| Web3 top-liquidity | pool, protocol, liquidity | token × snapshot | probe/sample only | high | pool discovery, liquidity | no executable depth history |
| Web3 token trades | trade time, price, amount, wallet/tag when returned | token × trade | probe capability; not in current saved panel | high until available_time and pagination are validated | flow reconstruction, wallet, graph, event | current dataset has no usable wallet trade panel |
| Local `alpha-lab-os` SQLite | candles, market_state, quotes, trades | local smoke run | short snapshots | source-specific | schema validation, quote/event pilot | Web3 smoke/demo, not CEX; trades empty |
| Binance Spot docs | klines, aggTrades, depth | symbol × time/trade/order book | documented | unknown until collected | CEX backbone, lead-lag, execution | no local historical file; not probed with Web3 key |
| Binance Futures docs | klines, funding, OI history, mark/index/premium | symbol × time | endpoint-specific documented | unknown until collected | market state, price discovery, relative value | no local historical file; executable depth absent |
| Wallet/entity data | holdings, trades, exits, balances, PnL | wallet × asset × time | unavailable | blocked | participant skill, graph diffusion | must acquire prior closed trades with availability clocks |

## Field-level research rules

- `event_time` describes when the economic observation occurred.
- `observed_time` describes when the source observed it.
- `available_time` is the earliest research-usable time.
- `ingest_time` describes local persistence.
- Outcome fields are never promoted into triggers without an explicit known-at audit.
- Relative value is research-only until executable depth, fees, spread, gas/funding, latency, and capacity are measured.
