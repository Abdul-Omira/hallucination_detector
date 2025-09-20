# Contributing to Hallucination Detector

Thanks for your interest — contributions of all kinds are welcome!

## Quick start

1. Fork and clone the repo
2. Install with dev extras
   ```bash
   pip install -e .[dev]
   ```
3. Run tests
   ```bash
   pytest -q
   ```
4. (Optional) Install schema extras for JSON Schema tests
   ```bash
   pip install -e .[schema]
   ```

## Development workflow

- Create a feature branch from `main`
- Keep changes focused and minimal; update or add tests
- Ensure quality gates pass locally:
  ```bash
  ruff check .
  black --check .
  isort . --check-only
  mypy src tests
  pytest -q
  ```
- Open a Pull Request; CI runs the same checks and coverage

## Project style and conventions

- Python 3.10+
- Public APIs are type‑annotated
- Imports: stdlib, third‑party, then local; absolute imports
- Naming: snake_case functions/vars, PascalCase classes, UPPER_SNAKE constants
- Errors: library code shouldn’t print; return `Detection` or raise specific exceptions; only catch broad exceptions at CLI boundaries
- Detection semantics: `severity` is `info|warn|block`; `block` overrides; accumulate `reasons` deterministically
- JSON handling: parsing errors must include reason `invalid_json`
- CLI prints JSON only; avoid extra stdout noise in library code

## Running examples

See `examples/README.md` and run the scripts with:
```bash
python examples/custom_detector.py
python examples/json_schema_validation.py
```

## Reporting issues

- Use the GitHub issue templates (bug/feature)
- Include steps to reproduce, expected vs actual results, and environment details

## Code of Conduct

Be kind and constructive. The maintainers reserve the right to moderate.
