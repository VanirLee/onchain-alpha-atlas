# Hypothesis system

Hypotheses are YAML first-class objects under `configs/hypotheses/`. They state
the question, mechanism, primitives, entities, data dependencies, method,
horizons, falsification, classification, and status. Python runners read these
files; research logic is not hard-coded as an implicit factor contract.

`artifacts/experiment_registry.parquet` records every executed variant,
including blocked and failed attempts. Classifications are
`PRE_SPECIFIED`, `EXPLORATORY`, or `POST_HOC`.
