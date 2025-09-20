from __future__ import annotations

import json

from hallucination_detector import registry
from hallucination_detector.detector import Detection, detect_text, guard_overconfidence


def make_detector(name: str, severity: str = "warn"):
    def _det(_text: str) -> Detection:
        return Detection(False, [f"{name}_reason"], severity)  # type: ignore[arg-type]

    return _det


def test_override_never_downgrades():
    registry.clear_registry()
    registry.register_detector("blk", make_detector("blk", severity="block"))
    checks = registry.build_checks(include=["blk"], severity_overrides={"blk": "warn"})
    res = checks[0]("{}")
    assert not res.ok and res.severity == "block" and res.reasons == ["blk_reason"]


def test_include_unknown_is_ignored_and_exclude_builtin():
    registry.clear_registry()
    checks = registry.build_checks(
        include=["unknown", "json", "numeric_claims"], exclude=["numeric_claims"]
    )
    # should only include json
    assert len(checks) == 1
    assert checks[0]("{}").ok  # valid json passes


def test_dedup_reasons_when_same_detector_runs_twice():
    # Construct checks where same detector appears twice
    text = json.dumps({"x": "This is definitely true."})
    res = detect_text(text, checks=[guard_overconfidence, guard_overconfidence])
    assert not res.ok and res.reasons.count("overconfident_no_citations") == 1
