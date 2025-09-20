import json
import os
import subprocess
import sys

import pytest


def _has_jsonschema():
    try:
        import jsonschema  # noqa: F401

        return True
    except Exception:
        return False


def _run_cli(args, input_text=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        os.path.join(os.getcwd(), "src") + os.pathsep + env.get("PYTHONPATH", "")
    )
    cmd = [sys.executable, "-m", "hallucination_detector.cli", "detect"] + args
    proc = subprocess.run(
        cmd,
        input=input_text.encode() if isinstance(input_text, str) else input_text,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout.decode().strip(), proc.stderr.decode()


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_cli_schema_block_on_failure(tmp_path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {"a": {"type": "number"}},
                "required": ["a"],
            }
        )
    )
    code, out, err = _run_cli(["--text", "{}", "--schema", str(schema_path)])
    assert code == 2
    data = json.loads(out)
    assert data["severity"] == "block" and "schema_validation_failed" in data["reasons"]


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_cli_schema_warn_on_failure_when_configured(tmp_path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {"a": {"type": "number"}},
                "required": ["a"],
            }
        )
    )
    code, out, err = _run_cli(
        [
            "--text",
            "{}",
            "--schema",
            str(schema_path),
            "--schema-severity",
            "warn",
        ]
    )
    assert code == 1
    data = json.loads(out)
    assert data["severity"] == "warn" and "schema_validation_failed" in data["reasons"]


def test_cli_schema_unavailable():
    if _has_jsonschema():
        pytest.skip("jsonschema available in environment")
    # file read will fail differently, keep minimal
    code, out, err = _run_cli(["--text", "{}", "--schema", "nonexistent.json"])
    # We expect a warn and a specific reason
    assert code == 1
    data = json.loads(out)
    assert (
        data["severity"] == "warn"
        and "schema_validation_unavailable" in data["reasons"]
    )
