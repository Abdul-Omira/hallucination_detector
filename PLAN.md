# Project Plan — Hallucination Detector

Live checklist of work to make this package robust and best‑in‑class. I will keep this updated as tasks complete.

## Phase 1 — Core correctness & UX
- [ ] Detection: deterministic aggregation (stable order, de‑dup reasons)
- [ ] Detection: proper severity escalation (info < warn < block)
- [ ] Detection: narrow JSON errors to JSONDecodeError
- [ ] CLI: accept --file and stdin input; keep JSON‑only output
- [ ] CLI: add --pretty flag to format JSON output
- [ ] CLI: exit codes (0 ok, 1 warn, 2 block)
- [ ] Tests: detectors (json, overconfidence), aggregation, severity
- [ ] Tests: CLI (text/file/stdin, pretty, exit codes)
- [ ] Tooling: add ruff/black/isort/mypy configs (no new deps required to run)
- [ ] CI: run lint, type‑check, tests (extend existing workflow)

## Phase 2 — Capability & extensibility
- [ ] Numeric claims detector (reuses existing FACT_PATTERN)
- [ ] Optional JSON Schema validation (extra dependency)
- [ ] Plugin registry: pluggable detectors + configuration

## Phase 3 — Quality & distribution
- [ ] Evaluation harness + basic metrics
- [ ] Docs: README examples, architecture, contributing
- [ ] Release workflow (tags → build → GitHub Release)

Progress updates will be added inline by ticking boxes and annotating changes as they land.
