# Assumptions and explicit limits

- API capability is discovered from the local project hints and bounded read-only probes. Unknown endpoints remain `unknown`; no endpoint is invented from memory.
- The user-stated nominal quota is about 50 QPS. The default sustained target is 40 QPS and is further capped by the configured limiter. Endpoint concurrency is separately bounded.
- Binance Web3 endpoint request weight may differ by endpoint. The limiter treats each request as one scheduling token until observed headers or documented weights are available.
- A POST request is permitted only when the endpoint is in the read-only allowlist (for example batch market `price-info`); all transaction/write-like paths are rejected.
- If an API response does not expose event time, `observed_at` is the knowledge timestamp. Later-updated outcome fields are excluded from features.
- The initial run is a research sample, not a 90–180 day production backfill. Any insufficiency is preserved in the report.
- Cost figures are proxy costs unless executable depth/quotes are separately collected. Backtests never claim executable arbitrage.
- Existing files under sibling projects may be used only as `local_reference` evidence; they are not silently merged into current live observations.
