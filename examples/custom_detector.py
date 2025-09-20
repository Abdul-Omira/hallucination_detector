#!/usr/bin/env python3
"""
Custom detector example using the registry.

Run:
  python examples/custom_detector.py

Requires project installed (editable is fine):
  pip install -e .[dev]
"""
from __future__ import annotations

import json

from hallucination_detector import (
    build_checks,
    clear_registry,
    detect_text,
    register_detector,
)
from hallucination_detector.detector import Detection


def no_todo_detector(text: str) -> Detection:
    if "TODO" in text:
        return Detection(False, ["todo_found"], "warn")
    return Detection(True, [])


def main() -> None:
    clear_registry()
    register_detector("no_todo", no_todo_detector)

    checks = build_checks(include=["json", "no_todo"])  # run JSON first, then custom

    samples = [
        '{"x":"ok"}',
        '{"x":"TODO: fill this"}',
    ]

    for s in samples:
        res = detect_text(s, checks=checks)
        print(json.dumps({"input": s, "result": res.__dict__}, ensure_ascii=False))


if __name__ == "__main__":
    main()
