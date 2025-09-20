import pytest

from hallucination_detector.detector import (
    InvalidSchema,
    SchemaValidationUnavailable,
    make_schema_guard,
)


def _has_jsonschema():
    try:
        import jsonschema  # noqa: F401

        return True
    except Exception:
        return False


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_schema_guard_block_on_failure():
    schema = {
        "type": "object",
        "properties": {"a": {"type": "number"}},
        "required": ["a"],
    }
    guard = make_schema_guard(schema, severity="block")
    res = guard("{}")
    assert (
        not res.ok
        and res.severity == "block"
        and "schema_validation_failed" in res.reasons
    )


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_schema_guard_ok_on_valid():
    schema = {
        "type": "object",
        "properties": {"a": {"type": "number"}},
        "required": ["a"],
    }
    guard = make_schema_guard(schema)
    res = guard('{"a": 1}')
    assert res.ok


def test_schema_guard_unavailable_raises():
    if _has_jsonschema():
        pytest.skip("jsonschema available in environment")
    with pytest.raises(SchemaValidationUnavailable):
        make_schema_guard({"type": "object"})


def test_invalid_schema_raises_when_jsonschema_present():
    if not _has_jsonschema():
        pytest.skip("jsonschema not installed")
    with pytest.raises(InvalidSchema):
        make_schema_guard({"type": "not-a-real-type"})
