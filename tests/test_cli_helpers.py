from hallucination_detector.cli import _parse_severity_overrides, _split_csv


def test_split_csv_various_inputs():
    assert _split_csv(None) == []
    assert _split_csv([]) == []
    assert _split_csv(["a,b", " c , d "]) == ["a", "b", "c", "d"]


def test_parse_severity_overrides_filters_and_normalizes():
    pairs = ["foo", "name=DEBUG", " a = warn ", "empty=", "=warn", "b=block"]
    out = _parse_severity_overrides(pairs)
    assert out == {"a": "warn", "b": "block"}
