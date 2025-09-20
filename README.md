# Hallucination Detector

Pragmatic guardrails for AI agent outputs. It’s small, predictable, and easy to wire into CLIs, backends, or batch evaluators.

- Deterministic results: stable reason order, de‑duped, severity escalation (info < warn < block)
- Batteries included: CLI + Python API + CI templates
- Extensible: plug your own detectors; optional JSON Schema validation

## Install
- Dev (recommended for hacking): `pip install -e .[dev]`
- With JSON Schema validation: `pip install -e .[schema]`

Python 3.10+.

## CLI
Detect issues in a text blob (often JSON):

```bash
# OK
hd detect --text '{"x": 1}'

# Block: invalid JSON
hd detect --text 'not json' ; echo $?

# Warn: overconfidence without citation
hd detect --text '{"x":"This is definitely true."}'

# Validate against a JSON Schema (warn/block configurable)
hd detect --text '{}' --schema schema.json --schema-severity warn
```

Exit codes: `0` ok, `1` warn (not ok), `2` block

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
res = validate("{}")              # not ok, 'schema_validation_failed'
res = validate('{"a": 1}')       # ok
```

Validators are compiled and cached per schema for performance.

### Pluggable registry
```python
from hallucination_detector import (
  register_detector, clear_registry, list_detectors, build_checks, detect_text
)

# Register a custom detector
from hallucination_detector.detector import Detection
register_detector("no_todo", lambda s: Detection(False, ["todo_found"], "warn") if "TODO" in s else Detection(True, []))

# Build checks: include/exclude and severity overrides
checks = build_checks(include=["json", "no_todo"], severity_overrides={"no_todo": "block"})
res = detect_text('{"x":"has TODO"}', checks=checks)
```

## Development
- Tests: `pytest -q` (install `[schema]` extra to run schema tests)
- Lint/format/type: `ruff check .`, `black --check .`, `isort . --check-only`, `mypy src tests`
- Build: `pip install build && python -m build`

## License
MIT
