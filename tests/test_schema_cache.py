import json
import pytest


def _has_jsonschema():
    try:
        import jsonschema  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_schema_validator_caching():
    from hallucination_detector.detector import make_schema_guard, _VALIDATOR_CACHE  # type: ignore[attr-defined]

    # Clear cache (if present)
    _VALIDATOR_CACHE.clear()
    schema = {"type": "object", "properties": {"a": {"type": "number"}}, "required": ["a"]}

    # First build populates cache
    g1 = make_schema_guard(schema)
    size1 = len(_VALIDATOR_CACHE)
    assert size1 == 1

    # Second build with logically equal schema should reuse cache (no growth)
    schema_equiv = json.loads(json.dumps(schema))
    g2 = make_schema_guard(schema_equiv)
    size2 = len(_VALIDATOR_CACHE)
    assert size2 == 1

    # Guards both work and do not interfere
    assert not g1("{}").ok
    assert not g2("{}").ok


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_clear_schema_cache_helper():
    from hallucination_detector.detector import make_schema_guard
    from hallucination_detector import clear_schema_cache
    
    schema = {"type": "object", "properties": {"a": {"type": "number"}}, "required": ["a"]}
    # build once
    _ = make_schema_guard(schema)
    # clear via API
    clear_schema_cache()
    # build again — should repopulate without errors
    _ = make_schema_guard(schema)
