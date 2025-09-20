import argparse
import json
import sys
from typing import Optional, Dict, List

from .detector import detect_text, make_schema_guard, SchemaValidationUnavailable, InvalidSchema
from . import registry


def _read_input(text: Optional[str], file: Optional[str]) -> str:
    if file:
        if file == "-":
            return sys.stdin.read()
        with open(file, "r", encoding="utf-8") as f:
            return f.read()
    if text is not None:
        return text
    # Fallback: read from stdin if available
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit(64)


def _jsonschema_available() -> bool:
    try:
        import jsonschema  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def _split_csv(values: Optional[List[str]]) -> List[str]:
    if not values:
        return []
    out: List[str] = []
    for v in values:
        for part in v.split(","):
            p = part.strip()
            if p:
                out.append(p)
    return out


def _parse_severity_overrides(pairs: Optional[List[str]]) -> Dict[str, str]:
    if not pairs:
        return {}
    out: Dict[str, str] = {}
    for raw in pairs:
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            if "=" not in part:
                continue
            name, val = part.split("=", 1)
            name = name.strip()
            val = val.strip().lower()
            if name and val in {"warn", "block"}:
                out[name] = val
    return out


def main():
    p = argparse.ArgumentParser(prog="hd", description="Hallucination Detector CLI")
    sub = p.add_subparsers(dest="cmd")

    d = sub.add_parser("detect", help="Detect issues in a text blob")
    d.add_argument("--text", help="Text to check (often JSON)")
    d.add_argument("--file", help="File path to read (use '-' for stdin)")
    d.add_argument("--schema", help="JSON Schema file path (enables schema validation)")
    d.add_argument("--schema-severity", choices=["warn", "block"], default="block", help="Severity when schema validation fails")
    d.add_argument("--include", action="append", help="Comma-separated detector names to include (order respected)")
    d.add_argument("--exclude", action="append", help="Comma-separated detector names to exclude")
    d.add_argument("--severity", dest="severity_overrides", action="append", help="Per-detector severity override entries like 'name=warn|block' (repeatable or comma-separated)")
    d.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    args = p.parse_args()

    if args.cmd == "detect":
        data = _read_input(args.text, args.file)

        checks = None
        # If schema is provided, we prioritize schema validation and ignore registry flags
        if args.schema:
            if not _jsonschema_available():
                print(json.dumps({"ok": False, "reasons": ["schema_validation_unavailable"], "severity": "warn"}), flush=True)
                raise SystemExit(1)
            try:
                with open(args.schema, "r", encoding="utf-8") as f:
                    schema = json.load(f)
            except Exception:
                print(json.dumps({"ok": False, "reasons": ["invalid_schema"], "severity": "block"}), flush=True)
                raise SystemExit(2)
            try:
                schema_guard = make_schema_guard(schema, severity=args.schema_severity)  # type: ignore[arg-type]
                checks = [schema_guard]
            except SchemaValidationUnavailable:
                print(json.dumps({"ok": False, "reasons": ["schema_validation_unavailable"], "severity": "warn"}), flush=True)
                raise SystemExit(1)
            except InvalidSchema:
                print(json.dumps({"ok": False, "reasons": ["invalid_schema"], "severity": "block"}), flush=True)
                raise SystemExit(2)
        else:
            # Build checks from registry based on CLI flags if any were provided
            include = _split_csv(getattr(args, "include", None))
            exclude = _split_csv(getattr(args, "exclude", None))
            sev_map = _parse_severity_overrides(getattr(args, "severity_overrides", None))
            if include or exclude or sev_map:
                checks = registry.build_checks(
                    include=include or None,
                    exclude=exclude or None,
                    severity_overrides=sev_map or None,
                )

        res = detect_text(data, checks=checks) if checks is not None else detect_text(data)
        payload = res.__dict__
        if args.pretty:
            print(json.dumps(payload, indent=2))
        else:
            print(json.dumps(payload, separators=(",", ":")))
        # Exit codes: 0 ok, 1 warn (not ok), 2 block
        code = 2 if res.severity == "block" else (1 if not res.ok else 0)
        raise SystemExit(code)

    p.print_help()


if __name__ == "__main__":
    main()
