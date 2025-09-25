import pytest

from hallucination_detector import registry
from hallucination_detector.detector import Detection


def _ok(_text: str) -> Detection:
    return Detection(True, [])


def test_register_invalid_name_raises():
    with pytest.raises(ValueError):
        registry.register_detector("", _ok)
