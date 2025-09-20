from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Sequence, Set
import json
import re

Severity = Literal["info", "warn", "block"]

@dataclass
class Detection:
    ok: bool
    reasons: List[str]
    severity: Severity = "info"
    patches: Dict[str, Any] | None = None

FACT_PATTERN = re.compile(r"\b(\d{4})\b|\b([0-9]+\.?[0-9]*)%\b")

def guard_json(text: str) -> Detection:
    try:
        json.loads(text)
        return Detection(True, [])
    except json.JSONDecodeError:
        return Detection(False, ["invalid_json"], "block")

def guard_overconfidence(text: str) -> Detection:
    confident = any(k in text.lower() for k in ["definitely", "certainly", "undeniably"])
    cites = ("http://" in text) or ("https://" in text) or ("doi.org" in text)
    if confident and not cites:
        return Detection(False, ["overconfident_no_citations"], "warn")
    return Detection(True, [])

def detect_text(text: str, checks: Sequence[Callable[[str], Detection]] | None = None) -> Detection:
    detectors = list(checks) if checks is not None else [guard_json, guard_overconfidence]
    reasons: List[str] = []
    seen: Set[str] = set()
    severity: Severity = "info"
    order = {"info": 0, "warn": 1, "block": 2}
    for check in detectors:
        r = check(text)
        if not r.ok:
            for reason in r.reasons:
                if reason not in seen:
                    seen.add(reason)
                    reasons.append(reason)
            if order[r.severity] > order[severity]:
                severity = r.severity
    return Detection(ok=(len(reasons) == 0), reasons=reasons, severity=severity)
