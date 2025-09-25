import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Sequence, Set

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


FACT_PATTERN = re.compile(r"\b\d{4}\b|\b\d{1,3}%(?!\w)")

# Configurable list of overconfidence keywords
CONFIDENT_KEYWORDS = [
    "definitely",
    "certainly",
    "undeniably",
    "absolutely",
    "undoubtedly",
    "clearly",
    "obviously",
]


def set_confident_keywords(keywords: List[str]) -> None:
    """Set the list of keywords that trigger overconfidence detection."""
    global CONFIDENT_KEYWORDS
    CONFIDENT_KEYWORDS = keywords


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
    confident = any(k in text.lower() for k in CONFIDENT_KEYWORDS)
    cites = ("http://" in text) or ("https://" in text) or ("doi.org" in text)
    if confident and not cites:
        return Detection(
            False,
            ["overconfident_no_citations"],
            "warn",
            {"suggestion": "Add a citation link to support the claim."},
        )
    return Detection(True, [])


def guard_contradictions(text: str) -> Detection:
    # Simple check for obvious contradictions like "A > B and B > A"
    contradictions = [
        r"A > B and B > A",
        r"true and false",
        r"yes and no",
        r"positive and negative",
        r"good and bad",
        r"all and some",
        r"none and some",
        r"always and sometimes",
        r"never and occasionally",
        # Add more as needed
    ]
    for pattern in contradictions:
        if re.search(pattern, text, re.IGNORECASE):
            return Detection(False, ["possible_contradiction"], "warn")
    return Detection(True, [])


def guard_logical_fallacies(text: str) -> Detection:
    # Simple check for common logical fallacies
    fallacies = [
        r"everyone (knows|thinks|agrees)",  # Ad populum
        r"obviously|clearly|of course",  # Appeal to obviousness (overlaps with overconfidence)
        r"either.*or.*no.*middle",  # False dichotomy
        r"you.*because.*you.*are",  # Ad hominem
        # Add more as needed
    ]
    for pattern in fallacies:
        if re.search(pattern, text, re.IGNORECASE):
            return Detection(False, ["possible_logical_fallacy"], "info")
    return Detection(True, [])


def guard_fact_check(text: str) -> Detection:
    # Stub for fact-checking integration
    # In future, call APIs like Wikidata or Google Fact Check
    # For now, flag if "fact" is mentioned without citation
    if "fact" in text.lower():
        cites = ("http://" in text) or ("https://" in text) or ("doi.org" in text)
        if not cites:
            return Detection(
                False,
                ["unverified_fact"],
                "warn",
                {"suggestion": "Verify with reliable source."},
            )
    return Detection(True, [])


def guard_numeric_claims(text: str) -> Detection:
    # Warn when numeric/percent patterns appear without any citation markers
    if FACT_PATTERN.search(text):
        cites = ("http://" in text) or ("https://" in text) or ("doi.org" in text)
        if not cites:
            return Detection(
                False,
                ["numeric_claims_without_citation"],
                "warn",
                {"suggestion": "Add a citation link to verify the numeric claim."},
            )
    return Detection(True, [])


def make_schema_guard(
    schema: Dict[str, Any],
    *,
    severity: Severity = "block",
) -> Callable[[str], Detection]:
    try:
        from jsonschema.exceptions import ValidationError
        from jsonschema.validators import Draft202012Validator
    except Exception as e:  # pragma: no cover - exercised via CLI skip
        raise SchemaValidationUnavailable("jsonschema package is not installed") from e

    key = None
    try:
        key = json.dumps(
            schema,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
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
        except ValidationError as e:
            sev: Severity = severity
            missing = []
            if hasattr(e, "absolute_path") and e.absolute_path:
                missing.append(".".join(str(p) for p in e.absolute_path))
            patches = {"missing_fields": missing} if missing else None
            return Detection(False, ["schema_validation_failed"], sev, patches)

    return guard


def load_custom_rules(rules_file: str) -> List[Callable[[str], Detection]]:
    """Load custom rules from YAML or JSON file."""
    try:
        import yaml
    except ImportError:
        yaml = None

    with open(rules_file, "r", encoding="utf-8") as f:
        if rules_file.endswith(".yaml") or rules_file.endswith(".yml"):
            if yaml is None:
                raise ImportError("PyYAML required for YAML rules")
            rules = yaml.safe_load(f)
        else:
            rules = json.load(f)

    detectors = []
    for rule in rules.get("rules", []):
        pattern = rule.get("pattern", "")
        severity = rule.get("severity", "warn")
        reason = rule.get("reason", "custom_rule_violation")
        require_citation = rule.get("require_citation", False)

        def make_detector(pat=pattern, sev=severity, rea=reason, cit=require_citation):
            def detector(text: str) -> Detection:
                if re.search(pat, text, re.IGNORECASE):
                    cites = "http://" in text or "https://" in text or "doi.org" in text
                    if not cit or not cites:
                        return Detection(False, [rea], sev)
                return Detection(True, [])

            return detector

        detectors.append(make_detector())

    return detectors


def detect_text(
    text: str,
    checks: Sequence[Callable[[str], Detection]] | None = None,
    skip_json: bool = False,
    custom_rules: Sequence[Callable[[str], Detection]] | None = None,
) -> Detection:
    detectors = (
        list(checks)
        if checks is not None
        else [
            guard_json,
            guard_overconfidence,
            guard_contradictions,
            guard_logical_fallacies,
            guard_fact_check,
            guard_numeric_claims,
        ]
    )
    if custom_rules:
        detectors.extend(custom_rules)  # type: ignore
    if skip_json and checks is None:
        detectors = [
            guard_overconfidence,
            guard_contradictions,
            guard_logical_fallacies,
            guard_fact_check,
            guard_numeric_claims,
        ] + (list(custom_rules) if custom_rules else [])
    reasons: List[str] = []
    seen: Set[str] = set()
    severity: Severity = "info"
    patches: Dict[str, Any] = {}
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
            if r.patches:
                patches.update(r.patches)
    return Detection(
        ok=(len(reasons) == 0),
        reasons=reasons,
        severity=severity,
        patches=patches or None,
    )


def detect_batch(
    texts: List[str],
    checks: Sequence[Callable[[str], Detection]] | None = None,
    skip_json: bool = False,
    custom_rules: Sequence[Callable[[str], Detection]] | None = None,
) -> List[Detection]:
    """Detect on a batch of texts with parallelism."""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(detect_text, t, checks, skip_json, custom_rules)
            for t in texts
        ]
        return [f.result() for f in futures]


def generate_report(results: List[Detection], format: str = "json") -> str:
    """Generate a summary report."""
    total = len(results)
    ok = sum(1 for r in results if r.ok)
    warns = sum(1 for r in results if not r.ok and r.severity == "warn")
    blocks = sum(1 for r in results if r.severity == "block")
    reasons = {}
    for r in results:
        for reason in r.reasons:
            reasons[reason] = reasons.get(reason, 0) + 1

    report = {
        "total_texts": total,
        "ok": ok,
        "warn": warns,
        "block": blocks,
        "reason_counts": reasons,
    }
    if format == "html":
        html = f"<h1>Report</h1><p>Total {total}, OK {ok}, Warn {warns}, Block {blocks}</p><ul>"
        for reason, count in reasons.items():
            html += f"<li>{reason}: {count}</li>"
        html += "</ul>"
        return html
    return json.dumps(report, indent=2)
