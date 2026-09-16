# Wallet observability

- wallet_count: 3057
- trade_count: 9299
- multi_trade_wallets: 1191
- single_trade_ratio: 0.6104023552502453
- median_trades_per_wallet: 1.0
- median_assets_per_wallet: 1.0
- chains: 4
- status: OBSERVABLE_BUT_SHORT

## Skill gate

- wallet_min: 50
- median_trades_min: 3
- history_days_min: 7
- wallet_count: 3057
- median_trades_per_wallet: 1.0
- history_days: 33
- status: FAIL
- reason: The observed tape is dominated by single-trade wallets and has short history.

Wallet identifiers are `(chain,address)`; EVM addresses are lowercased and non-EVM representations preserve case. Skill research is not promoted when the gate fails.
