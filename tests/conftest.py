import pathlib
import sys


def pytest_sessionstart(session):
    root = pathlib.Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        # Monkeypatch detector for tests in this process
        from typing import Any, cast

        import hallucination_detector.detector as det
        from hallucination_detector import _detector_new as new

        # Allow assignment across compatible signatures for tests
        det.detect_text = cast(Any, new.detect_text)
    except Exception:
        pass
