# Phase II Baseline

This document freezes the corrected research engine for Phase II. No architecture redesign is authorized unless a test or explicit validation identifies a bug.

- Generated: `2026-09-16T13:40:48.633374+00:00`
- Code hash: `1dad0332e01fe921118038af765a9e43da83e7a742db0e6d126d6a31d7e7d447`
- Dataset hash: `a8fb35ddbea197f5c34fc368dc7ad417365474f81fc53cb7394611ff7a19fa7c`
- Current assets: `112`
- Current universe label: `CURRENT-UNIVERSE-BACKFILL`; it is not a historical PIT listing universe.

## Frozen and validated

- canonical four-clock data model and `(chain, token_address)` identity
- exact timestamp PIT features/labels
- event study engine
- hypothesis and experiment registries
- lead-lag engine
- corrected IC/HAC and BH-FDR
- purged timestamp OOS
- non-overlapping baseline backtest
- read-only API client, limiter, checkpoint/cache, reporting, audit bundle

## Experimental

- volume-shock event detector and unmatched event response
- volume-to-return lead-lag
- market-state conditional response
- factor baseline and proxy cost model

## BLOCKED_BY_DATA

- wallet skill/entity persistence: no wallet trade/holding panel
- wallet-token temporal network diffusion: no real edge panel
- DEX-CEX/spot-perpetual relative value: no local CEX history or executable depth
- historical all-token PIT universe: current hot-token backfill only

API target remains `40.0` QPS or lower; no write endpoint is allowed.
