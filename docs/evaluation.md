# Evaluation

## Testing Strategy
- Unit tests per detector and aggregator (arrange/act/assert)
- CLI tests exercise stdin, files, flags, and exit codes
- Schema tests run when `[schema]` extra is installed
- Registry tests cover include/exclude, ordering, and severity overrides

## Running Tests
```bash
pytest -q                    # fast feedback
pytest -k "schema" -q       # focus subset
pytest tests/test_cli.py -q  # file selection
```

## Performance Notes
- JSON Schema validators are compiled once and cached by schema content
- Numeric/overconfidence checks run on raw text with low overhead

## Coverage
- Optional: `pip install pytest-cov` then `pytest --cov=hallucination_detector --cov-report=term-missing`

## Future Evaluation
- Synthetic corpora to stress detector thresholds
- Shadow‑mode against production logs (anonymized)
- Agreement analysis against human annotations
