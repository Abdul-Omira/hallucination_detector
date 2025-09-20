# How I Detect AI Agent Failures (and ship fixes before users notice)

**TL;DR:** Hallucinations aren’t bugs in the code; they’re missing guardrails in the system. This post ships a minimal, production‑grade detector: intercept responses, verify claims, and auto‑remediate. No drama—just engineering.

## The design goal
Catch high‑risk nonsense cheaply, without blocking legitimate creativity. Latency budget: <150ms p95; footprint: a single sidecar service or middleware.

## Failure modes to detect
- **Unsupported claims** (no provenance).
- **Contradictions** against retrieved facts or prior turns.
- **Unsafe actions** (tool call with missing preconditions).
- **Spec violations** (schema/regex/JSON failures).
- **Overconfidence** (hedged content presented as certain).

## Architecture (three layers)
1. **Syntactic Guards** — JSON schema, regexes, type checks.
2. **Semantic Verifiers** — retrieval‑augmented claim checks + NLI (natural language inference) for entailment/contradiction.
3. **Policy & Remediation** — downgrade to safer template, request clarifying info, or route to human.

```
app → agent → detector.middleware → (allow | repair | route)
```

## Minimal Python middleware
```python
# middleware/detector.py
from typing import Dict, Any, Tuple, List
import re, json

class DetectionResult:
    def __init__(self, ok: bool, reasons: List[str], severity: str = "info", patches: Dict[str, Any] | None = None):
        self.ok = ok
        self.reasons = reasons
        self.severity = severity
        self.patches = patches or {}

def json_shape_guard(text: str) -> DetectionResult:
    try:
        obj = json.loads(text)
    except Exception:
        return DetectionResult(False, ["invalid_json"], "block")
    return DetectionResult(True, [])

FACT_PATTERN = re.compile(r"\b(\d{{4}})\b|\b([0-9]+\.?[0-9]*)%\b")  # crude: dates and percents

def overconfident_without_citations(text: str) -> DetectionResult:
    confident = any(k in text.lower() for k in ["definitely", "certainly", "undeniably"])
    cites = ("http://" in text) or ("https://" in text) or ("doi.org" in text)
    if confident and not cites:
        return DetectionResult(False, ["overconfident_no_citations"], "warn")
    return DetectionResult(True, [])

def run_all(text: str) -> DetectionResult:
    checks = [json_shape_guard, overconfident_without_citations]
    reasons = []
    severity = "info"
    for check in checks:
        r = check(text)
        if not r.ok:
            reasons += r.reasons
            severity = "block" if r.severity == "block" else severity
    return DetectionResult(ok=(len(reasons)==0), reasons=reasons, severity=severity)

def enforce(text: str) -> Tuple[str, DetectionResult]:
    r = run_all(text)
    if r.ok:
        return text, r
    # trivial remediation: wrap in disclaimer and request clarification
    patched = {"message": "Uncertain output — needs verification", "original": text, "actions": ["request_clarification"]}
    return json.dumps(patched), r
```

Wire it as WSGI/ASGI middleware or as a FastAPI dependency. Start simple, measure, then add semantic checks.

## Adding semantic verification (RAG + NLI)
- Retrieve top‑k passages for each claim.
- Run an **entailment classifier** (NLI) on (passage, claim).
- Compute an **evidence score**; block or downgrade below threshold.
- Cache aggressively; pro‑tip: hash claims to dedupe checks.

## Telemetry (what to log)
- Detector decisions (`allow/repair/route`) + reasons.
- Latency breakdown per layer.
- False positives/negatives from human feedback.

## KPIs that matter
- **False positive rate ≤ 5%** — don’t drown users in warnings.
- **MTTR ≤ 10 min** — time to ship a rule/patch after a miss.
- **Errors prevented / month** — the scoreboard that compounds trust.

## Definition of done
- Detector runs in shadow mode on live traffic for 48 hours.
- No P0 regressions; latency p95 within budget.
- Dashboard shows live KPIs; docs include definitions + caveats.

**Code & roadmap:** github.com/<your-org>/hallucination-detector — issues welcome.
