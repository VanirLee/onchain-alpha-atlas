# Phase II Research Report

Generated: 2026-09-16T13:44:16.203923+00:00

## Executive Summary

Phase II activated real event, information-transmission, market-state, and corrected-baseline research without redesigning the frozen PIT/statistics/backtest engine. The current panel is still a current hot-token backfill, not a historical all-token PIT universe.

- Event-study rows: `12`; threshold-horizon q<0.05 rows after BH: `4` (exploratory only).
- State-conditional rows: `9`.
- Registry experiments: `21`; statuses: `{"EXPLORATORY": 18, "BLOCKED_BY_DATA": 3}`.
- Local CEX inventory rows usable as CEX: `4`.
- Factor baseline rows: `90`.

## Family A — Participant Information Advantage

H003 is `BLOCKED_BY_DATA`: the current saved dataset has no wallet trade/holding panel with prior closed-trade outcomes and available-time semantics. No wallet skill or wallet-return finding is claimed.

## Family B — Event Response

H001 uses the pre-declared 90/95/97.5/99 volume threshold grid and 1h/4h/24h exact timestamp outcomes. The unmatched response design is exploratory and not causal; overlapping episodes and current-universe selection remain material limitations.

[
  {
    "detector_percentile": 97.5,
    "horizon": 24,
    "n_events": 304,
    "mean_return": -0.05008077705838937,
    "p_value": 0.00011294239376364191,
    "fdr_adjusted_p_value": 0.00045176957505456763
  },
  {
    "detector_percentile": 99.0,
    "horizon": 24,
    "n_events": 304,
    "mean_return": -0.05008077705838937,
    "p_value": 0.00011294239376364191,
    "fdr_adjusted_p_value": 0.00045176957505456763
  },
  {
    "detector_percentile": 90.0,
    "horizon": 24,
    "n_events": 667,
    "mean_return": -0.04025807563197011,
    "p_value": 6.348106011086582e-06,
    "fdr_adjusted_p_value": 7.617727213303899e-05
  },
  {
    "detector_percentile": 95.0,
    "horizon": 24,
    "n_events": 421,
    "mean_return": -0.0380023537730786,
    "p_value": 0.0006064661759442358,
    "fdr_adjusted_p_value": 0.0018193985278327075
  },
  {
    "detector_percentile": 95.0,
    "horizon": 4,
    "n_events": 561,
    "mean_return": -0.005972229836305077,
    "p_value": 0.12142429182892309,
    "fdr_adjusted_p_value": 0.2914183003894154
  },
  {
    "detector_percentile": 97.5,
    "horizon": 4,
    "n_events": 400,
    "mean_return": -0.004901064186193725,
    "p_value": 0.32455109909716556,
    "fdr_adjusted_p_value": 0.4868266486457483
  }
]

The BH-adjusted event rows are hypothesis-screening outputs, not OOS-supported alpha. A significant in-sample p-value is not sufficient for execution research.

## Family C — Information Transmission

H002 estimates volume-to-future-return lead-lag with HAC regression at 1h/4h/24h. It is predictive association, not causality. A synchronized CEX spot/perpetual panel is required to test a true cross-venue transmission path.

## Family D — Market State Dependence

H004 conditions event response on pre-event liquidity and volatility buckets. Current state summaries:

[
  {
    "state_variable": "liquidity_state",
    "state_bucket": "LOW",
    "mean_return": -0.015213344846083951
  },
  {
    "state_variable": "volatility_state",
    "state_bucket": "HIGH",
    "mean_return": -0.01717292153577708
  },
  {
    "state_variable": "volatility_state",
    "state_bucket": "LOW",
    "mean_return": -0.009604007255919486
  }
]

These are exploratory conditional associations; the history is insufficient for an OOS-supported regime claim.

## Family E — Relative Value / Price Discovery

H005 is `BLOCKED_BY_DATA`: no local Binance Spot/Futures history, synchronized DEX-CEX mapping, or executable depth was found. Capacity is not estimated.

## Family F — Network Diffusion

H006 is `BLOCKED_BY_DATA`: no wallet-token edge panel is available. The temporal graph engine remains schema-ready and as-of safe, but no diffusion result is fabricated.

## Baseline Factor Family

H007 retains the corrected factor panel as a benchmark. It is not the Phase II primary objective. Its IC/HAC, BH-FDR, purged OOS, and leave-one-chain-out outputs remain in the formal baseline reports.

## Falsification, OOS, and tradeability

Future-data invariance tests pass and all threshold variants are retained. No Phase II finding is `OOS_SUPPORTED` or `ECONOMICALLY_VIABLE`; there is no execution candidate. The current run reports `INSUFFICIENT_OOS_HISTORY` for new event/state variants rather than forcing a split.

## Highest-value next data

1. Synchronized Binance Spot klines/trades/depth and USDⓈ-M Futures klines/funding/OI/mark-index data.
2. Paginated Web3 token trades with wallet/address fields and reliable available timestamps.
3. Wallet holdings/balances plus closed-trade exits and PnL available before measurement time.

## Limitations

Current hot-token selection and survivor bias; short/non-synchronized history; no executable depth, latency, gas/funding, or cross-venue mapping; wallet/entity families blocked.
