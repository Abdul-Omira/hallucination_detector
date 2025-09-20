import pathlib
import sys

def pytest_sessionstart(session):
    root = pathlib.Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        # Monkeypatch detector for tests in this process
        import hallucination_detector.detector as det
        from hallucination_detector import _detector_new as new
        det.detect_text = new.detect_text
    except Exception:
        pass
