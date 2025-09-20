import json

from hallucination_detector import registry
from hallucination_detector.detector import detect_text


def test_reason_order_and_block_escalation():
    # not json triggers block, plus overconfidence and numeric claims add reasons
    text = "not json definitely 95%"
    res = detect_text(text)
    assert not res.ok and res.severity == "block"
    assert res.reasons[:3] == [
        "invalid_json",
        "overconfident_no_citations",
        "numeric_claims_without_citation",
    ]


essential_json = json.dumps({"x": "95%"})


def test_exclude_numeric_claims_allows_percent_without_citation():
    registry.clear_registry()
    # built-ins minus numeric claims
    checks = registry.build_checks(exclude=["numeric_claims"])
    res = detect_text(essential_json, checks=checks)
    assert res.ok
