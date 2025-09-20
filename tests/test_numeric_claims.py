import json

from hallucination_detector.detector import detect_text


def test_numeric_claims_warn_without_citation():
    text = json.dumps({"msg": "The success rate was 95% in 2024."})
    r = detect_text(text)
    assert not r.ok
    assert r.severity == "warn"
    assert "numeric_claims_without_citation" in r.reasons


def test_numeric_claims_ok_with_citation():
    text = json.dumps({"msg": "The success rate was 95% in 2024 https://example.com"})
    r = detect_text(text)
    assert r.ok
