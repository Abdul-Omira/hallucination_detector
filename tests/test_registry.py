from __future__ import annotations

import json

from hallucination_detector import registry
from hallucination_detector.detector import Detection


def make_fail_detector(name: str):
    def _fail(_text: str) -> Detection:
        return Detection(False, [f"{name}_failed"], "warn")

    return _fail


def test_registry_default_order_and_registration():
    registry.clear_registry()
    # default order
    names = registry.list_detectors()
    assert names[:6] == ["json", "overconfidence", "contradictions", "logical_fallacies", "fact_check", "numeric_claims"]

    # add a custom detector and ensure it comes last by default
    registry.register_detector("custom", make_fail_detector("custom"))
    checks = registry.build_checks()
    # Verify the last detector is our custom one by invoking on good JSON
    text = json.dumps({"x": "safe"})
    # Run through all except the last to ensure ok for json, overconfidence, etc.
    # and no custom issues
    for fn in checks[:-1]:
        assert fn(text).ok
    # Last one should fail with our reason
    last_res = checks[-1](text)
    assert (
        not last_res.ok
        and last_res.reasons == ["custom_failed"]
        and last_res.severity == "warn"
    )


def test_registry_include_exclude_and_overrides():
    registry.clear_registry()
    registry.register_detector("a", make_fail_detector("a"))
    registry.register_detector("b", make_fail_detector("b"))

    checks = registry.build_checks(
        include=["b", "json", "a"],
        exclude=["json"],
        severity_overrides={"b": "block"},
    )
    # Order should be ["b", "a"], and b escalated to block
    assert len(checks) == 2
    r_b = checks[0]("{}")
    assert not r_b.ok and r_b.severity == "block" and r_b.reasons == ["b_failed"]
    r_a = checks[1]("{}")
    assert not r_a.ok and r_a.severity == "warn" and r_a.reasons == ["a_failed"]
