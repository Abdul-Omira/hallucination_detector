from hallucination_detector.detector import detect_text


def test_invalid_json():
    r = detect_text("not json")
    assert not r.ok and "invalid_json" in r.reasons
