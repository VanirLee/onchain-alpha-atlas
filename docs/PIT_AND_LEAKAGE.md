# PIT and leakage rules

- Exact target timestamps are required for time horizons; missing targets are
  NaN.
- State features use only current or prior clock-time observations.
- `available_time` is the strict research cutoff. Backfilled historical API
  data are labelled as backfill limitations rather than prospective evidence.
- Wallet skill at t uses closed trades with exit/measurement time strictly
  before t and available by t.
- Graph snapshots filter edges by event and available time as of the decision.
- Future-data invariance is tested by appending adversarial future rows and
  comparing all historical outputs.
