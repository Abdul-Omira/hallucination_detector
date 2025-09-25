import io
import json
import runpy
import sys
import tempfile
from pathlib import Path

import pytest

from hallucination_detector import cli
from hallucination_detector.detector import SchemaValidationUnavailable


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


def test_inprocess_text_ok(capsys):
    code = run_main_argv(["hd", "detect", "--text", '{"a":1}'])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_inprocess_text_warn_and_pretty(capsys):
    code = run_main_argv(
        ["hd", "detect", "--text", '{"x":"This is definitely true."}', "--pretty"]
    )
    assert code == 1
    out = capsys.readouterr().out
    assert out.startswith("{\n  ") and "overconfident_no_citations" in out


def test_inprocess_stdin_fallback_reads_when_no_tty(capsys):
    # No flags -> read from stdin
    # Our _read_input treats missing isatty as non-tty
    code = run_main_argv(["hd", "detect"], stdin_text='{"a":1}')
    assert code == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True


def test_inprocess_dash_stdin(capsys):
    code = run_main_argv(["hd", "detect", "--file", "-"], stdin_text="not json")
    assert code == 2
    assert "invalid_json" in capsys.readouterr().out


def test_inprocess_include_exclude_and_severity(capsys):
    # Only run numeric_claims and escalate it to block
    payload = json.dumps({"msg": "The success rate was 95% in 2024."})
    code = run_main_argv(
        [
            "hd",
            "detect",
            "--text",
            payload,
            "--include",
            "numeric_claims",
            "--severity",
            "numeric_claims=block",
        ]
    )
    assert code == 2
    data = json.loads(capsys.readouterr().out)
    assert (
        data["severity"] == "block"
        and "numeric_claims_without_citation" in data["reasons"]
    )


def test_inprocess_schema_unavailable_warns(capsys, monkeypatch):
    # Force the "schema unavailable" branch irrespective of the environment
    monkeypatch.setattr(cli, "_jsonschema_available", lambda: False)
    code = run_main_argv(["hd", "detect", "--text", "{}", "--schema", "x.json"])
    assert code == 1
    data = json.loads(capsys.readouterr().out)
    assert (
        data["severity"] == "warn"
        and "schema_validation_unavailable" in data["reasons"]
    )


def test_inprocess_file_path_reads_warns(capsys):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "input.json"
        p.write_text('{"x":"This is definitely true."}', encoding="utf-8")
        code = run_main_argv(["hd", "detect", "--file", str(p)])
        assert code == 1
        out = json.loads(capsys.readouterr().out)
        assert "overconfident_no_citations" in out["reasons"]


def test_inprocess_no_input_exit_64():
    class TTY:
        def isatty(self):
            return True

        def read(self):  # pragma: no cover - should not be called
            return ""

    old = sys.stdin
    try:
        sys.stdin = TTY()
        # Invoke detect with no text/file so _read_input triggers exit 64
        code = run_main_argv(["hd", "detect"])
        assert code == 64
    finally:
        sys.stdin = old


@pytest.mark.skipif(
    not hasattr(cli, "make_schema_guard"), reason="cli.make_schema_guard not available"
)
@pytest.mark.skipif(
    not hasattr(sys, "modules"), reason="environment lacks monkeypatch capability"
)
def test_inprocess_schema_make_guard_unavailable_branch(monkeypatch, capsys, tmp_path):
    # Simulate jsonschema available but guard creation raising SchemaValidationUnavailable
    monkeypatch.setattr(cli, "_jsonschema_available", lambda: True)

    def _boom(_schema, severity="block"):
        raise SchemaValidationUnavailable()

    monkeypatch.setattr(cli, "make_schema_guard", _boom)

    # Provide a real schema file so file-read succeeds and guard creation is exercised
    schema_path = tmp_path / "schema.json"
    schema_path.write_text("{}", encoding="utf-8")

    code = run_main_argv(["hd", "detect", "--text", "{}", "--schema", str(schema_path)])
    assert code == 1
    data = json.loads(capsys.readouterr().out)
    assert (
        data["severity"] == "warn"
        and "schema_validation_unavailable" in data["reasons"]
    )


def test_module_entrypoint_executes_main(capsys, monkeypatch):
    # Execute module as __main__ to cover the entrypoint guard
    old_argv = sys.argv[:]
    try:
        sys.argv = ["python", "detect", "--text", "{}"]
        with pytest.raises(SystemExit) as exc:
            runpy.run_module("hallucination_detector.cli", run_name="__main__")
        assert exc.value.code == 0
        assert json.loads(capsys.readouterr().out)["ok"] is True
    finally:
        sys.argv = old_argv
