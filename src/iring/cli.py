"""iring: YouTube link -> iPhone ringtone."""

import asyncio
import tempfile
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from iring.audio import AudioError, check_tools, download, duration_ms, make_ringtone
from iring.clip import ClipError, resolve_clip
from iring.phone import NoPhoneError, PhoneError, delete_ringtones, push_ringtone, read_library
from iring.tones import clean_title, find_tones

DEFAULT_OUT = Path.home() / "Music" / "iring"
BACKUP_DIR = Path.home() / "Library" / "Application Support" / "iring" / "backups"

console = Console()
err = Console(stderr=True)

app = typer.Typer(
    help="Make an iPhone ringtone from a YouTube video and put it on the connected iPhone.",
    epilog="Times look like 90, 1:05 or 1:02:03. Ringtones can be at most 40s.",
    add_completion=True,
    no_args_is_help=True,
)


def safe_filename(name: str) -> str:
    return "".join("_" if c in '/:\\' else c for c in name).strip() or "ringtone"


def make(url: str, start: str | None, end: str | None, name: str | None, out: Path) -> tuple[Path, str, int]:
    clip_start, clip_duration = resolve_clip(start, end)
    check_tools()

    with tempfile.TemporaryDirectory(prefix="iring-") as tmp:
        with console.status("Downloading audio"):
            source, title = download(url, Path(tmp))
        name = name or clean_title(title)
        console.print(f"[green]✓[/] Downloaded [bold]{title}[/]")

        with console.status(f"Cutting {clip_start:g}s to {clip_start + clip_duration:g}s and encoding"):
            out.mkdir(parents=True, exist_ok=True)
            m4r = out / f"{safe_filename(name)}.m4r"
            total_ms = make_ringtone(source, m4r, clip_start, clip_duration)
        console.print(f"[green]✓[/] Saved {m4r}")

    return m4r, name, total_ms


def push(m4r: Path, name: str, total_ms: int) -> None:
    with console.status("Copying to iPhone"):
        try:
            device, replaced = asyncio.run(push_ringtone(m4r, name, total_ms, BACKUP_DIR))
        except NoPhoneError:
            console.print(f"[yellow]![/] No iPhone connected. Plug it in and run: iring '{m4r}'")
            return
    if replaced:
        console.print(f"[green]✓[/] Replaced the previous '{name}'")
    console.print(f"[green]✓[/] [bold]{name}[/] is on {device}. Find it in Settings > Sounds & Haptics > Ringtone.")


def show_list() -> None:
    with console.status("Reading ringtones from iPhone"):
        device, library = asyncio.run(read_library(BACKUP_DIR))
    tones = library.get("Ringtones", {})
    if not tones:
        console.print(f"No custom ringtones on {device}.")
        return
    table = Table(title=f"Custom ringtones on {device}", title_justify="left")
    table.add_column("Name")
    table.add_column("Length", justify="right")
    for entry in sorted(tones.values(), key=lambda e: e.get("Name", "").casefold()):
        table.add_row(entry.get("Name", "?"), f"{entry.get('Total Time', 0) / 1000:.0f}s")
    console.print(table)


def delete(query: str, yes: bool) -> None:
    with console.status("Reading ringtones from iPhone"):
        device, library = asyncio.run(read_library(BACKUP_DIR))
    matches = find_tones(library, query)
    if not matches:
        raise PhoneError(f"no custom ringtone on {device} matches {query!r} (see iring --list)")

    for name in matches.values():
        console.print(f"  • {name}")
    if not yes and not typer.confirm(f"Delete {len(matches)} ringtone(s) from {device}?"):
        raise typer.Abort()

    with console.status("Deleting"):
        asyncio.run(delete_ringtones(list(matches), BACKUP_DIR))
    console.print(f"[green]✓[/] Deleted {len(matches)} ringtone(s) from {device}.")


@app.command()
def iring(
    source: Annotated[str | None, typer.Argument(help="YouTube URL, or a .m4r file to push", show_default=False)] = None,
    start: Annotated[str | None, typer.Option("--start", "-s", help="Where the clip starts", show_default="0:00")] = None,
    end: Annotated[str | None, typer.Option("--end", "-e", help="Where the clip ends", show_default="start + 30s")] = None,
    name: Annotated[str | None, typer.Option("--name", "-n", help="Name shown in Settings", show_default="video title")] = None,
    out: Annotated[Path, typer.Option("--out", "-o", help="Where to keep .m4r files")] = DEFAULT_OUT,
    no_push: Annotated[bool, typer.Option("--no-push", help="Only make the .m4r, don't copy it to the phone")] = False,
    list_: Annotated[bool, typer.Option("--list", "-l", help="List custom ringtones on the iPhone")] = False,
    delete_: Annotated[str | None, typer.Option("--delete", "-d", help="Delete ringtones whose name matches (case-insensitive)", show_default=False)] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Don't ask before deleting")] = False,
) -> None:
    """Make an iPhone ringtone from a YouTube video and put it on the connected iPhone."""
    try:
        if list_ or delete_ is not None:
            if source or (list_ and delete_ is not None):
                raise typer.BadParameter("use --list or --delete on its own")
            show_list() if list_ else delete(delete_, yes)
            return

        if source is None:
            raise typer.BadParameter("give a YouTube URL or a .m4r file")

        if source.lower().endswith(".m4r"):
            m4r = Path(source).expanduser()
            if not m4r.is_file():
                raise AudioError(f"no such file: {m4r}")
            name, total_ms = name or m4r.stem, duration_ms(m4r)
        else:
            m4r, name, total_ms = make(source, start, end, name, out)

        if not no_push:
            push(m4r, name, total_ms)
    except (ClipError, AudioError, PhoneError, NoPhoneError) as e:
        err.print(f"[red]error:[/] {e}")
        raise typer.Exit(1)


def main() -> None:
    app()
