from app.core.config import get_settings

_high = None
_low = None


def high_threshold() -> float:
    global _high
    if _high is None:
        _high = get_settings().high_confidence_threshold
    return _high


def low_threshold() -> float:
    global _low
    if _low is None:
        _low = get_settings().low_confidence_threshold
    return _low


def set_thresholds(high: float | None = None, low: float | None = None) -> None:
    global _high, _low
    if high is not None:
        _high = high
    if low is not None:
        _low = low
