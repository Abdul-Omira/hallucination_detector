import json
import os
import subprocess
import sys
import tempfile


def _run_cli(args, input_text=None):
    env = os.environ.copy()
    # Ensure src is importable for the module invocation
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
    return proc.returncode, proc.stdout.decode().strip()


def test_cli_text_ok():
    code, out = _run_cli(["--text", '{"a":1}'])
    assert code == 0
    data = json.loads(out)
    assert data["ok"] is True


def test_cli_text_block():
    code, out = _run_cli(["--text", "not json"])
    assert code == 2
    data = json.loads(out)
    assert data["severity"] == "block" and "invalid_json" in data["reasons"]


def test_cli_text_warn():
    code, out = _run_cli(["--text", '{"x":"This is definitely true."}'])
    assert code == 1


def test_cli_file_and_pretty():
    # Write-then-close so Windows does not hold a write lock during subprocess
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "input.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"x":"This is definitely true."}')
        code, out = _run_cli(["--file", path, "--pretty"])
        assert code == 1
        assert "\n  " in out.replace("\r\n", "\n")  # pretty JSON


def test_cli_stdin_dash():
    code, out = _run_cli(["--file", "-"], input_text="not json")
    assert code == 2
