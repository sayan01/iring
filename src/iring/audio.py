"""Downloading audio with yt-dlp and encoding ringtones with ffmpeg."""

import shutil
import subprocess
from pathlib import Path

FADE_SECONDS = 1


class AudioError(RuntimeError):
    pass


def check_tools() -> None:
    missing = [tool for tool in ("yt-dlp", "ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        raise AudioError(f"missing {', '.join(missing)}, install with: brew install {' '.join(missing)}")


def _run(args: list[str], what: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()[-1:] or ["no error output"]
        raise AudioError(f"{what} failed: {detail[0]}")
    return result.stdout


def download(url: str, workdir: Path) -> tuple[Path, str]:
    """Download the best audio stream of a single video. Returns (file, title)."""
    out = _run(
        [
            "yt-dlp",
            "--no-playlist",
            "--quiet",
            "--no-warnings",
            "-f",
            "bestaudio",
            "--no-simulate",
            "--print",
            "title",
            "--print",
            "after_move:filepath",
            "-o",
            str(workdir / "source.%(ext)s"),
            url,
        ],
        "download",
    )
    lines = out.strip().splitlines()
    if len(lines) < 2:
        raise AudioError(f"download failed: unexpected yt-dlp output {out!r}")
    return Path(lines[-1]), lines[0]


def duration_ms(path: Path) -> int:
    out = _run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        "reading duration",
    )
    return round(float(out.strip()) * 1000)


def make_ringtone(source: Path, dest: Path, start: float, duration: float) -> int:
    """Encode the clip as an AAC .m4r with a short fade-out. Returns its length in ms."""
    fade = (
        ["-af", f"afade=t=out:st={duration - FADE_SECONDS:g}:d={FADE_SECONDS}"] if duration > 2 * FADE_SECONDS else []
    )
    _run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-ss",
            f"{start:g}",
            "-i",
            str(source),
            "-t",
            f"{duration:g}",
            *fade,
            "-vn",
            "-ar",
            "44100",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-f",
            "ipod",
            str(dest),
        ],
        "encoding",
    )
    length = duration_ms(dest) if dest.exists() and dest.stat().st_size else 0
    if length == 0:
        dest.unlink(missing_ok=True)
        raise AudioError("the clip is empty, is --start past the end of the track?")
    return length
