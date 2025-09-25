from __future__ import annotations

from collections import OrderedDict
from typing import (
    Callable,
    Dict,
    List,
    Mapping,
    Sequence,
)

from .detector import (
    Detection,
    Severity,
    guard_contradictions,
    guard_fact_check,
    guard_json,
    guard_logical_fallacies,
    guard_numeric_claims,
    guard_overconfidence,
)

# User-defined detectors registry (in insertion order)
_USER_DETECTORS: "OrderedDict[str, Callable[[str], Detection]]" = OrderedDict()

_BUILTIN_ORDER: List[str] = [
    "json",
    "overconfidence",
    "contradictions",
    "logical_fallacies",
    "fact_check",
    "numeric_claims",
]


def _builtin_detectors() -> Dict[str, Callable[[str], Detection]]:
    return {
        "json": guard_json,
        "overconfidence": guard_overconfidence,
        "contradictions": guard_contradictions,
        "logical_fallacies": guard_logical_fallacies,
        "fact_check": guard_fact_check,
        "numeric_claims": guard_numeric_claims,
    }


def register_detector(name: str, fn: Callable[[str], Detection]) -> None:
    """Register or replace a detector under a unique name.

    Detectors should accept a string and return a Detection.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("Detector name must be a non-empty string")
    _USER_DETECTORS[name] = fn


def clear_registry() -> None:
    """Clear user-registered detectors (built-ins remain available)."""
    _USER_DETECTORS.clear()


def list_detectors(include_builtin: bool = True) -> List[str]:
    names: List[str] = []
    if include_builtin:
        names.extend(_BUILTIN_ORDER)
    names.extend(_USER_DETECTORS.keys())
    return names


def _wrap_with_severity(
    name: str,
    fn: Callable[[str], Detection],
    target: Severity,
) -> Callable[[str], Detection]:
    order = {"info": 0, "warn": 1, "block": 2}

    def wrapped(text: str) -> Detection:
        res = fn(text)
        if not res.ok:
            current = res.severity
            new = current if order[current] >= order[target] else target
            if new is not current:
                return Detection(
                    ok=res.ok,
                    reasons=list(res.reasons),
                    severity=new,
                    patches=res.patches,
                )
        return res

    return wrapped


def build_checks(
    *,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
    severity_overrides: Mapping[str, Severity] | None = None,
) -> List[Callable[[str], Detection]]:
    """Build an ordered list of detector callables.

    - include: if provided, use these names in this exact order
    - exclude: omit these names
    - severity_overrides: escalate severities for these detectors (never downgrades)
    """
    builtins = _builtin_detectors()
    combined: Dict[str, Callable[[str], Detection]] = {**builtins, **_USER_DETECTORS}

    if include is not None:
        ordered_names = [n for n in include if n in combined]
    else:
        ordered_names = [n for n in _BUILTIN_ORDER if n in combined]
        ordered_names.extend([n for n in _USER_DETECTORS.keys() if n in combined])

    if exclude:
        excluded = set(exclude)
        ordered_names = [n for n in ordered_names if n not in excluded]

    checks: List[Callable[[str], Detection]] = []
    for name in ordered_names:
        fn = combined[name]
        if severity_overrides and name in severity_overrides:
            fn = _wrap_with_severity(name, fn, severity_overrides[name])
        checks.append(fn)
    return checks
