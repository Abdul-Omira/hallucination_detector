import sys

from hallucination_detector import cli


def test_cli_no_args_prints_help(capsys):
    old = sys.argv[:]
    try:
        sys.argv = ["hd"]
        cli.main()
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "Hallucination Detector CLI" in out
    assert "usage: hd" in out
