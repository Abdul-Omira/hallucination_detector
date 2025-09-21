import os
import pathlib
import sys


def pytest_sessionstart(session):
    root = pathlib.Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    # Optional: allow testing against the experimental detector implementation
    # Opt-in via env var to keep default coverage focused on the stable path
    if os.getenv("HD_USE_EXPERIMENTAL_DETECTOR"):
        try:
            from typing import Any, cast

            import hallucination_detector.detector as det
            from hallucination_detector import _detector_new as new

            det.detect_text = cast(Any, new.detect_text)
        except Exception:
            pass
