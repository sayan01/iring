import pytest

from iring.clip import ClipError, parse_time, resolve_clip


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("0", 0),
        ("90", 90),
        ("1:05", 65),
        ("01:05", 65),
        ("1:05.5", 65.5),
        ("1:02:03", 3723),
    ],
)
def test_parse_time(text, seconds):
    assert parse_time(text) == seconds


@pytest.mark.parametrize("text", ["", "abc", "1:60", "-5", "1::2", "1:2:3:4"])
def test_parse_time_rejects_garbage(text):
    with pytest.raises(ClipError):
        parse_time(text)


def test_default_clip_is_first_30_seconds():
    assert resolve_clip(None, None) == (0, 30)


def test_start_only_gives_30_seconds_from_start():
    assert resolve_clip("1:05", None) == (65, 30)


def test_start_and_end():
    assert resolve_clip("1:05", "1:35") == (65, 30)


def test_end_only_starts_at_zero():
    assert resolve_clip(None, "0:20") == (0, 20)


def test_40_seconds_is_allowed():
    assert resolve_clip("0:10", "0:50") == (10, 40)


def test_longer_than_40_seconds_is_rejected():
    with pytest.raises(ClipError, match="40"):
        resolve_clip("0:00", "0:41")


def test_end_must_be_after_start():
    with pytest.raises(ClipError):
        resolve_clip("1:00", "0:30")
