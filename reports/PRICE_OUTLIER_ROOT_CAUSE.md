# Price Outlier Root-Cause Analysis

Outlier rows: **19**. A row is included if any <=60m signed response has absolute simple return above 50%, or its API-vs-paired-leg ratio is outside [0.1, 10]. The API-vs-USD ratio is not itself an error because API price is pair-denominated.

| Root-cause class | Count | Share |
|---|---:|---:|
| `H_UNKNOWN_REQUIRES_INDEPENDENT_QUOTE` | 14 | 73.68% |
| `C_TOKEN_AMOUNT_OR_DECIMALS` | 3 | 15.79% |
| `A_API_PRICE_VS_PAIRED_PRICE_MISMATCH` | 2 | 10.53% |

Classification is conservative: rows requiring an independent Binance Web3 price/candle at the exact trade timestamp remain `H_UNKNOWN_REQUIRES_INDEPENDENT_QUOTE`; they are not relabelled as true market moves.
