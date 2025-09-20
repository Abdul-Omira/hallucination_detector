import argparse
import json
import sys
from typing import Optional

from .detector import detect_text


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


def main():
    p = argparse.ArgumentParser(prog="hd", description="Hallucination Detector CLI")
    sub = p.add_subparsers(dest="cmd")

    d = sub.add_parser("detect", help="Detect issues in a text blob")
    d.add_argument("--text", help="Text to check (often JSON)")
    d.add_argument("--file", help="File path to read (use '-' for stdin)")
    d.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    args = p.parse_args()

    if args.cmd == "detect":
        data = _read_input(args.text, args.file)
        res = detect_text(data)
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
