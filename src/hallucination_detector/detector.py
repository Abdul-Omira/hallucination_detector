from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Sequence, Set
import json
import re

Severity = Literal["info", "warn", "block"]


class SchemaValidationUnavailable(Exception):
    pass


class InvalidSchema(Exception):
    pass


@dataclass
class Detection:
    ok: bool
    reasons: List[str]
    severity: Severity = "info"
    patches: Dict[str, Any] | None = None


FACT_PATTERN = re.compile(r"\b(\d{4})\b|\b([0-9]+(?:\.[0-9]+)?)%(?!\w)")

# Cache compiled JSON Schema validators by canonicalized schema string
_VALIDATOR_CACHE: Dict[str, Any] = {}

def clear_schema_cache() -> None:
    _VALIDATOR_CACHE.clear()


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


def guard_numeric_claims(text: str) -> Detection:
    # Warn when numeric/percent patterns appear without any citation markers
    if FACT_PATTERN.search(text):
        cites = ("http://" in text) or ("https://" in text) or ("doi.org" in text)
        if not cites:
            return Detection(False, ["numeric_claims_without_citation"], "warn")
    return Detection(True, [])


def make_schema_guard(schema: Dict[str, Any], *, severity: Severity = "block") -> Callable[[str], Detection]:
    try:
        from jsonschema.exceptions import ValidationError
        from jsonschema.validators import Draft202012Validator
    except Exception as e:  # pragma: no cover - exercised via CLI skip
        raise SchemaValidationUnavailable("jsonschema package is not installed") from e

    key = None
    try:
        key = json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except TypeError:
        key = None

    validator = None
    if key is not None and key in _VALIDATOR_CACHE:
        validator = _VALIDATOR_CACHE[key]
    else:
        try:
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema)
        except Exception as e:
            raise InvalidSchema("Provided schema is not a valid JSON Schema") from e
        if key is not None:
            _VALIDATOR_CACHE[key] = validator

    def guard(text: str) -> Detection:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return Detection(False, ["invalid_json"], "block")
        try:
            validator.validate(data)  # type: ignore[union-attr]
            return Detection(True, [])
        except ValidationError:
            sev: Severity = severity
            return Detection(False, ["schema_validation_failed"], sev)

    return guard


def detect_text(text: str, checks: Sequence[Callable[[str], Detection]] | None = None) -> Detection:
    detectors = list(checks) if checks is not None else [guard_json, guard_overconfidence, guard_numeric_claims]
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
