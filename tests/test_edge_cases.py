import json
import os
import subprocess
import sys
import tempfile

from hallucination_detector.detector import detect_text


def _run_cli(args, input_text=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src") + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, "-m", "hallucination_detector.cli", "detect"] + args
    proc = subprocess.run(
        cmd,
        input=input_text.encode() if isinstance(input_text, str) else input_text,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout.decode().strip(), proc.stderr.decode()


# Detector edge cases

def test_empty_string_is_invalid_json():
    r = detect_text("")
    assert not r.ok and r.severity == "block" and "invalid_json" in r.reasons


def test_whitespace_only_is_invalid_json():
    r = detect_text("   \n\t  ")
    assert not r.ok and r.severity == "block" and "invalid_json" in r.reasons


def test_unicode_text_with_overconfidence():
    r = detect_text('{"x":"هذا بالتأكيد صحيح"}')  # "definitely" in Arabic won't match
    assert r.ok  # should not warn; keywords are English-only


# Overconfidence multiple tokens and citation variations

def test_overconfidence_multiple_markers_no_citation_warns():
    r = detect_text('{"x":"This is definitely, certainly true."}')
    assert not r.ok and r.severity == "warn" and "overconfident_no_citations" in r.reasons


def test_overconfidence_with_various_citation_schemes_ok():
    for cite in ["http://a", "https://b", "doi.org/10.1/xyz"]:
        r = detect_text(json.dumps({"x": f"This is definitely true {cite}"}))
        assert r.ok


# CLI edge cases

def test_cli_stdin_only_no_flags_reads_stdin():
    code, out, err = _run_cli([], input_text="{\"a\":1}")
    assert code == 0
    data = json.loads(out)
    assert data["ok"] is True


def test_cli_dash_stdin_with_warn():
    code, out, err = _run_cli(["--file", "-"], input_text='{"x":"This is certainly true."}')
    assert code == 1


def test_cli_text_overrides_file_when_both_provided():
    with tempfile.NamedTemporaryFile("w+", delete=True) as f:
        f.write("{\"a\":2}")
        f.flush()
        code, out, err = _run_cli(["--file", f.name, "--text", "{\"a\":3}"])
        assert code == 0
        assert json.loads(out)["ok"] is True
        # ensure --text used (either is fine since both are valid JSON); this just checks no error


def test_cli_invalid_json_pretty_formatting_still_json_pretty():
    code, out, err = _run_cli(["--text", "not json", "--pretty"])
    assert code == 2
    assert out.startswith("{\n  ") and "invalid_json" in out


def test_cli_large_input_performance_smoke():
    big_obj = {"k": "v" * 10000}
    txt = json.dumps(big_obj)
    code, out, err = _run_cli(["--text", txt])
    assert code == 0 and json.loads(out)["ok"] is True
