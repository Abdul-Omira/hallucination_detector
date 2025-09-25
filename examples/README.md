# Examples

Runnable snippets demonstrating common usage patterns. Ensure you have the project installed in editable mode first:

```bash
pip install -e .[dev]
# For schema examples:
# pip install -e .[schema]
```

## 1) Custom detector via registry

Registers a simple detector and composes it with built‑ins.

Run:

```bash
python examples/custom_detector.py
```

## 2) JSON Schema validation

Validates input against a Draft 2020‑12 schema using the optional `jsonschema` extra.

Run:

```bash
python examples/json_schema_validation.py
```

## 3) Logical fallacies detection

Demonstrates detection of common logical fallacies like ad populum or false dichotomy.

Run:

```bash
python examples/logical_fallacies.py
```

## 4) CLI quick tour

These mirror README examples; shown here for convenience.

```bash
# OK
hd detect --text '{"x": 1}'

# Block: invalid JSON
hd detect --text 'not json' ; echo $?

# Warn: overconfidence without citation
hd detect --text '{"x":"This is definitely true."}'

# Numeric claims without citations (warn)
hd detect --text '{"x":"Success rate was 95% in 2024."}'

# Registry flags: include/exclude/escalate
hd detect --text '{"x":"definitely 95%"}' --severity overconfidence=block,numeric_claims=block

# Schema validation (takes precedence)
# (optional) pip install -e .[schema]
python - <<'PY'
import json, tempfile, os
schema = {"type":"object","properties":{"a":{"type":"number"}},"required":["a"]}
fd, path = tempfile.mkstemp(suffix='.json'); os.close(fd)
open(path,'w').write(json.dumps(schema)); print('schema at', path)
PY
# Replace <schema.json> with the printed path
hd detect --text '{}' --schema <schema.json> --schema-severity warn
```
