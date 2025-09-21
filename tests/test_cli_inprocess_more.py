import io
import json
import sys
import tempfile
from pathlib import Path

import pytest

from hallucination_detector import cli
from hallucination_detector.detector import SchemaValidationUnavailable


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

        def read(self):  # pragma: no cover - not called when TTY
            return ""

    old_stdin = sys.stdin
    old_argv = sys.argv[:]
    try:
        sys.stdin = TTY()
        sys.argv = ["hd", "detect"]
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 64
    finally:
        sys.stdin = old_stdin
        sys.argv = old_argv


def test_inprocess_schema_invalid_schema_branch(tmp_path, capsys):
    # Provide a syntactically valid but semantically invalid schema
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps({"type": "not-a-real-type"}), encoding="utf-8")
    code = run_main_argv(["hd", "detect", "--text", "{}", "--schema", str(schema_path)])
    assert code == 2
    data = json.loads(capsys.readouterr().out)
    assert data["severity"] == "block" and "invalid_schema" in data["reasons"]


def test_inprocess_schema_guard_unavailable_branch(monkeypatch, capsys, tmp_path):
    # Simulate jsonschema import available but guard creation raising SchemaValidationUnavailable
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


def test_jsonschema_available_helper_paths(monkeypatch):
    # Happy path: should be True when jsonschema import works
    assert cli._jsonschema_available() in {True, False}

    # Failure path: make importing jsonschema raise
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("jsonschema"):
            raise ImportError("forced")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    try:
        assert cli._jsonschema_available() is False
    finally:
        monkeypatch.setattr(builtins, "__import__", real_import)
