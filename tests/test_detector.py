from hallucination_detector.detector import detect_text


def test_logical_fallacies():
    # Ad populum
    r = detect_text("Everyone knows that.", skip_json=True)
    assert not r.ok and "possible_logical_fallacy" in r.reasons

    # OK text
    r = detect_text("This is a normal statement.", skip_json=True)
    assert r.ok
