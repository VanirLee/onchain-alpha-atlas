# Event research

`run_event_study` is generic: it accepts a standard events table and a market
state table, matches exact event/outcome timestamps, reports mean/median/AAR/CAR,
quantiles, hit rate, bootstrap confidence intervals, and overlap diagnostics.
The first real event family is H001 volume shocks detected from prior
clock-time volume history. It is exploratory and unmatched; it does not claim
causal alpha.
