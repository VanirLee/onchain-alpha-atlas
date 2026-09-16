# Network research

Temporal graph snapshots are filtered by `event_time`, `start_time`, and
`available_time` as of a decision timestamp. This prevents future co-trading
edges from altering historical centrality. The current run has no real wallet
trade edge panel, so `network_results.parquet` is explicitly
`BLOCKED_BY_DATA`.
