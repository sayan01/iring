"""Editing the iPhone's ringtone list (/iTunes_Control/iTunes/Ringtones.plist)."""

import copy
import random
import secrets
import string


def clean_title(title: str) -> str:
    """Video titles like "Artist - Song | Genre | Channel" become "Artist - Song"."""
    return title.split("|")[0].strip()


def empty_library() -> dict:
    return {"Ringtones": {}}


def _random_name() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=4))


def add_tone(library: dict, name: str, total_ms: int, existing_files: set[str]) -> tuple[dict, str, list[str]]:
    """Add a tone called `name` to a copy of `library`.

    Returns (updated library, file name to upload the tone as, file names of
    tones with the same name that were dropped from the list and should be
    deleted from the phone).
    """
    updated = copy.deepcopy(library)
    tones = updated.setdefault("Ringtones", {})

    removed = [fname for fname, entry in tones.items() if entry.get("Name") == name]
    for fname in removed:
        del tones[fname]

    taken = existing_files | set(tones) | set(removed)
    while (fname := f"{_random_name()}.m4r") in taken:
        pass

    tones[fname] = {
        "GUID": secrets.token_hex(8).upper(),
        "Name": name,
        "PID": random.randint(1, 2**63 - 1),
        "Protected Content": False,
        "Total Time": total_ms,
    }
    return updated, fname, removed


def find_tones(library: dict, query: str) -> dict[str, str]:
    """Tones whose name matches `query` (case-insensitive), as {file: name}.

    An exact name match wins; otherwise every name containing `query` matches.
    """
    tones = {fname: entry.get("Name", fname) for fname, entry in library.get("Ringtones", {}).items()}
    q = query.strip().casefold()
    exact = {f: n for f, n in tones.items() if n.casefold() == q}
    return exact or {f: n for f, n in tones.items() if q in n.casefold()}


def remove_tones(library: dict, fnames: list[str]) -> dict:
    updated = copy.deepcopy(library)
    for fname in fnames:
        updated.get("Ringtones", {}).pop(fname, None)
    return updated
