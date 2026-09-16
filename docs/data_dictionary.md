# Data dictionary

| Field | Meaning | PIT safety |
|---|---|---|
| `observed_at` | Local knowledge time for the response | safe anchor |
| `event_time` | Event/candle time supplied by the source | safe when source-defined |
| `effective_time` | Time at which the observation is economically applicable | must not be future-filled |
| `known_at` | Earliest time this field could be used | feature cutoff |
| `is_feature_safe` | Whether the field may enter a historical feature | false for outcome/final fields |
| `maxGain` / `future_peak_return` | Completed signal outcome | false, excluded |
| `payload_hash` | Content digest for idempotency/deduplication | audit |
| `request_params_hash` | Request identity digest | audit |
| `forward_return_*` | Future label, never a feature | label only |

All values are treated as strings at the raw layer and normalized at the Silver layer. Missing values stay missing; they are not backfilled from later snapshots.
