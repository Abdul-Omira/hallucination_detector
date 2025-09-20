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
def test_cli_schema_valid_data_ok(tmp_path):
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
    code, out, err = _run_cli(["--text", '{"a":1}', "--schema", str(schema_path)])
    assert code == 0
    data = json.loads(out)
    assert data["ok"] is True


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_cli_invalid_schema_file_content_block(tmp_path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text("not json schema")
    code, out, err = _run_cli(["--text", "{}", "--schema", str(schema_path)])
    assert code == 2
    data = json.loads(out)
    assert data["severity"] == "block" and "invalid_schema" in data["reasons"]
