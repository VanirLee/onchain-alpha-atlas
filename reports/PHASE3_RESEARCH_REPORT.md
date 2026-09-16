# Phase III Research Report

## Status

Phase III is data-first. R1–R4 are explicitly **BLOCKED_BY_DATA** in this run because no contract-level DEX/CEX paired identity was verified. No symbol-only join, future match, or synthetic trade data was used.

## Backbone measurements

- identity rows: 737; DEX_ONLY: 112; CEX_ONLY: 625; paired: 0.
- Web3 trade rows: 338; observed wallet count: 0.
- New CEX pilot bars: 6912; local reused CEX 1h rows: 10,653,582.
- Phase II event rows retained for audit: 477; independent 24h-cooldown episodes: 166.

## Research families

- R1 DEX/CEX price discovery: blocked; no verified paired panel.
- R2 DEX flow to CEX response: blocked for cross-venue inference; 338 trade rows are retained only as observable trade history.
- R3 spot/perpetual transmission: blocked for cross-venue inference; CEX pilot is collected independently.
- R4 matched event response: blocked for the Phase III paired event design; prior Phase II event result is not treated as replicated.

## Confirmation and OOS

No confirmation hypothesis was frozen for execution because the minimum paired-data gate failed. Therefore there is no OOS-supported or economically viable Phase III result.

## Limitations and next data priority

The binding bottleneck is exact DEX token contract ↔ Binance instrument mapping and continuous DEX trade history. Next priority is a verified contract map, then DEX trades and executable depth/slippage. Wallet, gas, bridge, and ML remain secondary.
