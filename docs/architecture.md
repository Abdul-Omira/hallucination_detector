# Architecture

The detector favors correctness and predictability over heuristics that drift.

## Pipeline
- Input: raw text (often JSON)
- Detectors: pure functions `text -> Detection`
- Aggregation: deterministic reason order + severity escalation (block overrides warn)
- Output: `Detection { ok, reasons[], severity }`

## Built‑in Detectors
- `guard_json`: parses JSON; on error returns `block` with reason `invalid_json`
- `guard_overconfidence`: flags phrases like “definitely/certainly/undeniably” unless citations exist
- `guard_numeric_claims`: flags years/percentages without citations

## JSON Schema Validation
- Factory `make_schema_guard(schema, severity)` compiles a Draft 2020‑12 validator once
- Validators are cached per canonicalized schema to avoid recompilation
- Failure reason: `schema_validation_failed`; severity as configured (warn/block)

## Severity Semantics
- `info < warn < block`
- Aggregator never downgrades severity
- Reasons are stable and de‑duplicated

## Plugin Registry
- Register custom detectors via `register_detector(name, fn)`
- Build a pipeline with `build_checks(include, exclude, severity_overrides)`
- Built‑ins order: `[json, overconfidence, numeric_claims]`, then user detectors

## CLI
- Subcommand `hd detect` pipes stdin/`--file`/`--text` to detectors
- JSON‑only output; exit code derived from final severity
