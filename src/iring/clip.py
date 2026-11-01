"""Turning --start/--end arguments into a clip that iOS will accept."""

DEFAULT_SECONDS = 30
MAX_SECONDS = 40  # iOS refuses ringtones longer than this


class ClipError(ValueError):
    pass


def parse_time(text: str) -> float:
    """Parse "90", "1:05", "1:05.5" or "1:02:03" into seconds."""
    parts = text.strip().split(":")
    if not 1 <= len(parts) <= 3:
        raise ClipError(f"invalid time {text!r}, expected e.g. 1:05")
    try:
        values = [float(p) for p in parts]
    except ValueError:
        raise ClipError(f"invalid time {text!r}, expected e.g. 1:05") from None
    if any(v < 0 for v in values) or any(v >= 60 for v in values[1:]):
        raise ClipError(f"invalid time {text!r}, expected e.g. 1:05")

    seconds = 0.0
    for value in values:
        seconds = seconds * 60 + value
    return seconds


def resolve_clip(start: str | None, end: str | None) -> tuple[float, float]:
    """Return (start, duration) in seconds."""
    start_s = parse_time(start) if start else 0
    if end is None:
        return start_s, DEFAULT_SECONDS

    duration = parse_time(end) - start_s
    if duration <= 0:
        raise ClipError("--end must be after --start")
    if duration > MAX_SECONDS:
        raise ClipError(f"clip is {duration:g}s long, iOS ringtones can be at most {MAX_SECONDS}s")
    return start_s, duration
