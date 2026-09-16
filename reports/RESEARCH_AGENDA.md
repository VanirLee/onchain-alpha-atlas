# Phase II Research Agenda

Core question: can observable participant behavior, market state, and cross-venue activity reveal information before prices fully incorporate it?

| Family | Hypothesis | Status | Primary data | Stop rule |
|---|---|---|---|---|
| Participant Information Advantage | H003 historical wallet skill persistence | BLOCKED_BY_DATA | wallet trades/holdings | acquire prior closed trades before token-return study |
| Event Response | H001 volume-shock response | EXPLORATORY | 112-asset Web3 market panel | threshold grid fixed at 90/95/97.5/99 |
| Information Transmission | H002 volume → future return | EXPLORATORY | chain-time market state | no causal language; require OOS before execution research |
| Market State Dependence | H004 event response by liquidity/volatility state | EXPLORATORY | event + pre-event state | no extra threshold mining |
| Relative Value / Price Discovery | H005 DEX-CEX convergence | BLOCKED_BY_DATA | CEX spot/perpetual/depth | no executable depth, no capacity claim |
| Network Diffusion | H006 wallet-token diffusion | BLOCKED_BY_DATA | wallet-token edges | minimum 300 wallets |
| Factor baseline | H007 corrected factors | EXPLORATORY | factor panel + exact labels | baseline only, not primary agenda |

All runs, including blocked and insignificant runs, are written to `artifacts/experiment_registry.parquet`.
