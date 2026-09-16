# Architecture

The platform has five separable layers:

1. Connectors and collectors: read-only API access and raw payload lineage.
2. Canonical PIT data: asset/entity/event/state/outcome tables with four
   clocks.
3. Hypothesis registry: YAML-defined research questions and experiment
   registry.
4. Research families: event study, entity skill, lead-lag, temporal graph,
   market state, relative value, prediction/sequence, and factor baseline.
5. Evaluation/reporting: inference, falsification, purged OOS, costs, gates,
   machine-readable outputs, and audit bundle.

No family depends on the factor engine. The factor engine is one baseline.
Wallet, CEX, and graph modules degrade to explicit `BLOCKED_BY_DATA` status.
