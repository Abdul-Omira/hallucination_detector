import io
import json
import sys

import pytest

from hallucination_detector import cli


def _has_jsonschema():
    try:
        import jsonschema  # noqa: F401

        return True
    except Exception:
        return False


def run_main_argv(argv, stdin_text=None):
    old_argv = sys.argv[:]
    old_stdin = sys.stdin
    try:
        sys.argv = argv
        if stdin_text is not None:
            sys.stdin = io.StringIO(stdin_text)
        with pytest.raises(SystemExit) as exc:
            cli.main()
        return exc.value.code
    finally:
        sys.argv = old_argv
        sys.stdin = old_stdin


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_inprocess_schema_valid_ok(tmp_path, capsys):
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
    code = run_main_argv(
        ["hd", "detect", "--text", '{"a":1}', "--schema", str(schema_path)]
    )
    assert code == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_inprocess_schema_warn_on_failure(tmp_path, capsys):
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
    code = run_main_argv(
        [
            "hd",
            "detect",
            "--text",
            "{}",
            "--schema",
            str(schema_path),
            "--schema-severity",
            "warn",
        ]
    )
    assert code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["severity"] == "warn" and "schema_validation_failed" in data["reasons"]


@pytest.mark.skipif(not _has_jsonschema(), reason="jsonschema not installed")
def test_inprocess_invalid_schema_file_block(tmp_path, capsys):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text("not json schema")
    code = run_main_argv(["hd", "detect", "--text", "{}", "--schema", str(schema_path)])
    assert code == 2
    data = json.loads(capsys.readouterr().out)
    assert data["severity"] == "block" and "invalid_schema" in data["reasons"]
