# On-chain Quant Research Report — Iteration 2

## Executive answer

The prior extreme returns were caused primarily by a price-unit mismatch: Binance Web3 `price` is paired-token-denominated, while `volume / token_quantity` is USD-normalized. The repaired research path uses USD-implied trade price for `P_event` and for the clock grid, while retaining API pair price for semantic auditing. Historical results remain discovery evidence and require forward confirmation.

## Measurement validation

- Price observations audited: **9299**.
- Price gate included: **9294**; excluded: **5**.
- API price semantic: paired-token price; research event price: `usd_value / abs(token_quantity)`.
- Future price: clock-time target matched on `source_trade_timestamp` within declared tolerance; missing target remains NaN.
- Independent Binance token candle at exact historical trade time: unavailable in the persisted sample.

## RQ1 — DEX trade information content

**Question.** Does signed trade direction predict future price response?

**Why economically important.** This distinguishes information-bearing flow from mechanical temporary pressure. **Sample.** 1m/5m/15m/60m valid trades and horizon-specific episodes. **Measurement validation.** Only price-gate-passing rows enter response analysis. **Method.** Own execution price anchor, clock-time future matching, cluster bootstrap and horizon-specific episode clusters.
**Economic magnitude.** 5m mean -21.29 bps, median 1.55 bps, trimmed mean 6.76 bps, signed-log mean 5.92 bps; 60m mean -4.41 bps, median -7.36 bps.
**Statistical uncertainty.** 5m episode CI [-37.33 bps, -8.55 bps], p=0.008872415900719776; asset×hour block CI [-33.66 bps, -6.65 bps], p=0.013481740224074978; hit rate=56.60%. The block result is the conservative dependence check.
**Cross-token stability.** See `artifacts/per_token_effects.parquet` and `70 LOTO rows`; **not established**. **Time stability.** `8 early/late rows`; not confirmation. **Falsification.** BH is applied across all registered R1 horizon variants; no q<0.10 is treated as confirmation. **Current answer.** NO ROBUST EVIDENCE IN CURRENT SAMPLE; response curve is approximately zero in robust central statistics, with short-horizon signs not stable. **Confidence.** Medium for the measurement repair, low for market inference. **What changes it.** New dates with the same frozen gate and source timestamps.

## RQ2 — Trade size and price impact

**Question.** Does USD trade size add information? **Method.** Five size groups, episode-balanced log-size regression, and top-decile versus middle-size matching within asset/day. **Economic magnitude.** 5m regression slope 9.04 bps per log(1+USD); matched top-decile minus middle -4.87 bps. The regression and matched variants are not stable and BH covers all registered size variants. **Controls.** Same asset/day matching; no future filters. **Current answer.** INCONCLUSIVE; no monotonic size-information result. **What changes it.** More repeated same-token/day matched states and observed volatility/intensity controls.

## RQ3 — Flow imbalance

**Question.** Does OFI predict future return rather than contemporaneous price pressure? **Sample.** 5052 window/horizon records. **Measurement validation.** Separate `pre_event_return_5m`, `contemporaneous_return`, and `forward_return`; future return begins after the flow timestamp. **Method.** 1m/5m/15m flow windows and 1m/5m/15m/60m future horizons. **Current answer.** INCONCLUSIVE; no robust evidence that flow is predictive beyond pressure. **Cross-token stability.** Per-token output is in `per_token_effects.parquet`.

## RQ4 — Response decay

**Question.** Is the path continuation, decay, reversal or none? **Method.** Full 1m/5m/15m/60m response curve and response-to-1m ratios. **Current answer.** The central response is small and the 60m horizon is near zero; a reliable continuation/decay/reversal classification is not identifiable without stronger independent price data and forward confirmation. If the 1m effect changes under new data, mark `RESILIENCE_NOT_IDENTIFIABLE` rather than forcing a decay label.

## RQ5 — Smart Money label validation

**Question.** Does the external label have incremental information? **Measurement validation.** Per-trade labels are now persisted with `label_available_time` and `is_pit_safe`. The bounded historical tag sample is current/forward-only; future-known labels are not used as historical features. **Current answer.** CURRENT/FORWARD LABEL ONLY / INSUFFICIENT SAMPLE; no Smart Money Alpha claim.

## RQ6 — Whale Holder label validation

The same PIT restriction applies. Current answer: INSUFFICIENT SAMPLE for historical incremental inference; collect label snapshots prospectively.

## RQ7 — Bundler label validation

The same PIT restriction applies. Current answer: INSUFFICIENT SAMPLE for historical incremental inference; no label meaning is assumed.

## RQ8 — High-activity wallets

Repeated-wallet comparison is sample-gated. Wallet count is not treated as information quality; only repeated response observations qualify.

## RQ9 — Wallet persistence

**Question.** Does past wallet information content predict later content? **Method.** Chronological first 60% versus last 40%, minimum five response observations, shrinkage required for small samples. **Current answer.** INCONCLUSIVE; pilot result is not confirmation and does not justify a SmartMoneyScore.

## RQ10 — Adoption and diffusion

Participation series contains 327 rows with unique wallets, new-wallet share, buyer HHI and subsequent return. Current answer: INCONCLUSIVE; no hand-tuned early-diffusion/late-crowding threshold was used.

## RQ11 — Participant concentration and crowding

Buyer concentration is retained as an observable, but current data do not establish a stable reversal relation. Current answer: INCONCLUSIVE.

## RQ12 — Cross-token robustness

Leave-one-token-out produced 70 rows across horizons. Current answer: INCONCLUSIVE; no claim survives as cross-token generalized evidence. Any future aggregate result that disappears when one asset is omitted must be marked FRAGILE_TOKEN_DEPENDENCE.

## Supported / inconclusive / rejected

- **Measurement supported:** API pair-price semantics and USD-implied P_event, subject to the documented lack of independent historical candle confirmation.
- **Inconclusive:** RQ1–RQ4 and RQ10–RQ12 market effects.
- **Current-label-only / insufficient:** RQ5–RQ7.
- **Rejected as a current research shortcut:** wallet skill/SmartMoneyScore before persistence is demonstrated; executable capacity claims without depth/impact data.

## Forward confirmation

All RQ1–RQ12 remain discovery-stage. The frozen horizons, variables, validation rules, controls and inference methods are recorded in `artifacts/RESEARCH_FREEZE.json`; new post-cutoff data belong to `FORWARD_CONFIRMATION`.

## Limitations and next three confirmations

1. Replicate the repaired response curve on newly appended trades.
2. Confirm paired-leg price semantics with exact-time Binance Web3 token price/candle observations where available.
3. Persist PIT-safe participant labels and repeated wallet histories before testing incremental information.

Superseded Phase IV microstructure results are excluded from this report.
