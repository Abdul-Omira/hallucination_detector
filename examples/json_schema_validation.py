#!/usr/bin/env python3
"""
JSON Schema validation example using the optional schema extra.

Run:
  # ensure extras installed
  # pip install -e .[schema]
  python examples/json_schema_validation.py
"""
from __future__ import annotations

import json
from typing import Any

from hallucination_detector.detector import make_schema_guard


def main() -> None:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {"a": {"type": "number"}},
        "required": ["a"],
        "additionalProperties": False,
    }

    validate = make_schema_guard(schema, severity="warn")

    samples = [
        "{}",  # invalid under schema
        '{"a": 1}',  # valid
        '{"a": "not number"}',  # invalid
    ]

    for s in samples:
        res = validate(s)
        print(json.dumps({"input": s, "result": res.__dict__}))


if __name__ == "__main__":
    main()
