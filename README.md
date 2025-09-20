# Hallucination Detector

Pragmatic guardrails for AI agent outputs — small, predictable, and easy to wire into CLIs, backends, or batch evaluators.

[![CI](https://github.com/Abdul-Omira/hallucination_detector/actions/workflows/ci.yml/badge.svg)](https://github.com/Abdul-Omira/hallucination_detector/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#-contributing) [![codecov](https://codecov.io/gh/Abdul-Omira/hallucination_detector/branch/main/graph/badge.svg)](https://codecov.io/gh/Abdul-Omira/hallucination_detector)

## Why this exists
- Deterministic results: stable reason order, de‑duped, severity escalation (`info < warn < block`).
- Simple: a few pure functions; zero heavy dependencies by default.
- Extensible: plug your own detectors; optional JSON Schema validation.
- Production‑friendly: CLI, Python API, CI templates, and tests.

If this is useful, please star the repo — it helps a lot!

---

## Try in 60 seconds
Python 3.10+ required.

```bash
# Clone + dev install
git clone https://github.com/Abdul-Omira/hallucination_detector.git
cd hallucination_detector
pip install -e .[dev]

# OK
hd detect --text '{"x": 1}'

# Block: invalid JSON
hd detect --text 'not json' ; echo $?

# Warn: overconfidence without citation
hd detect --text '{"x":"This is definitely true."}'

# Validate against a JSON Schema (warn/block configurable)
# (optional) pip install -e .[schema]
hd detect --text '{}' --schema schema.json --schema-severity warn
```

Exit codes: `0` ok, `1` warn (not ok), `2` block

---

## Features
- JSON guard: blocks invalid JSON with reason `invalid_json`.
- Overconfidence guard: warns on phrases like "definitely/certainly/undeniably" without citations.
- Numeric claims guard: warns on years/percentages without citations (e.g., "95%", "2024").
- JSON Schema validation: compile‑once, cached Draft 2020‑12 validators via `make_schema_guard()`.
- Pluggable registry: include/exclude detectors and escalate severities per detector.

---

## CLI usage
```bash
# Built‑ins (default order): json, overconfidence, numeric_claims
hd detect --text '{"x":"definitely 95%"}'

# Include/exclude specific detectors
hd detect --text '{"x":"95%"}' --exclude numeric_claims
hd detect --text '{"x":"text"}' --include json,overconfidence

# Escalate per‑detector severity
hd detect --text '{"x":"definitely 95%"}' --severity overconfidence=block,numeric_claims=block

# Schema validation (takes precedence over registry flags)
# (optional) pip install -e .[schema]
hd detect --text '{}' --schema schema.json --schema-severity warn
```

## Examples
- Custom detector via registry: `examples/custom_detector.py`
- JSON Schema validation demo: `examples/json_schema_validation.py`
- More commands: see `examples/README.md`


---

## Python API
```python
from hallucination_detector import detect_text

res = detect_text('{"x":"This is definitely true."}')
assert not res.ok
print(res.reasons)   # ['overconfident_no_citations']
print(res.severity)  # 'warn'
```

### JSON Schema
```python
from hallucination_detector import make_schema_guard

schema = {"type":"object","properties":{"a":{"type":"number"}},"required":["a"]}
validate = make_schema_guard(schema, severity="warn")
res = validate("{}")            # not ok, 'schema_validation_failed'
res = validate('{"a": 1}')     # ok
```

Validators are compiled and cached per schema for performance. You can clear the cache via:

```python
from hallucination_detector import clear_schema_cache
clear_schema_cache()
```

### Pluggable registry
```python
from hallucination_detector import (
  register_detector, clear_registry, list_detectors, build_checks, detect_text
)
from hallucination_detector.detector import Detection

# Register a custom detector
register_detector(
  "no_todo",
  lambda s: Detection(False, ["todo_found"], "warn") if "TODO" in s else Detection(True, [])
)

# Build checks: include/exclude and severity overrides
checks = build_checks(include=["json", "no_todo"], severity_overrides={"no_todo": "block"})
res = detect_text('{"x":"has TODO"}', checks=checks)
```

---

## Design principles
- Pure functions: detectors are `text -> Detection`.
- Predictable aggregation: deterministic reason order, no duplicates, severity only escalates.
- Minimal surface area: one CLI command, a small Python API.
- Practical performance: regex‑based checks + cached schema validators.

---

## Development
- Tests: `pytest -q` (install `[schema]` extra to run schema tests)
- Lint/format/type: `ruff check .`, `black --check .`, `isort . --check-only`, `mypy src tests`
- Build: `pip install build && python -m build`

---

## 🚀 Contributing
Contributions are very welcome — issues, examples, docs, and detectors!

- Good first steps: improve docs, add detector examples, expand tests.
- Run locally: `pip install -e .[dev]` then `pytest -q`.
- Open a PR from a feature branch; CI runs lint, type checks, and tests.
- See CONTRIBUTING.md for details.

If you like this project, please star it. It helps others discover it.

---

## Roadmap
- Registry flags in the CLI (done)
- JSON Schema validation (done)
- Additional built‑in detectors and examples
- GitHub Pages quick demo and docs

See CHANGELOG.md for notable changes.

---

## License
MIT

---

## Star history
[![Star History Chart](https://api.star-history.com/svg?repos=Abdul-Omira/hallucination_detector&type=Date)](https://star-history.com/#Abdul-Omira/hallucination_detector&Date)
