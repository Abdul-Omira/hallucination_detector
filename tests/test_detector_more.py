from hallucination_detector.detector import detect_text


def test_overconfidence_warn_without_citation():
    r = detect_text('{"msg":"This is definitely true."}')
    assert not r.ok
    assert r.severity == "warn"
    assert "overconfident_no_citations" in r.reasons


def test_overconfidence_ok_with_citation():
    r = detect_text('{"msg":"This is definitely true https://example.com"}')
    assert r.ok


def test_severity_block_overrides_warn():
    text = "not json but definitely true"
    r = detect_text(text)
    assert not r.ok
    assert r.severity == "block"
    # order stable and deduped
    assert r.reasons[0] == "invalid_json"
    assert r.reasons.count("invalid_json") == 1
