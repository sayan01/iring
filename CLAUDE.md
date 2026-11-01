# iring

CLI that turns a YouTube link into an iPhone ringtone and copies it straight onto a USB-connected iPhone,
with no Finder drag-and-drop. It can also list and delete custom ringtones on the phone.
User-facing docs are in `README.md`; this file is the context for working on the code.

## Usage

```sh
iring "<youtube url>"                       # first 30s, pushed to the phone
iring "<url>" -s 1:05 [-e 1:35]             # start (and end); without --end the clip is 30s; max 40s
iring "<url>" -n "Wake Up"                  # name shown in Settings (default: video title before first "|")
iring "<url>" --no-push [-o DIR]            # only make the .m4r (default dir ~/Music/iring)
iring path/to/Song.m4r [-n NAME]            # push an existing .m4r (name defaults to file stem)
iring --list                                # custom ringtones on the phone
iring --delete QUERY [-y]                   # delete by name: exact match wins, else case-insensitive substring; asks first
```

Times: `90`, `1:05`, `1:05.5`, `1:02:03`. `--list`/`--delete` must be used alone (no source).

## Layout

| File | Role |
|---|---|
| `src/iring/cli.py` | Typer app: one command `iring` with flags (no subcommands, so `iring <url>` works). Rich spinners/tables. Maps `ClipError`/`AudioError`/`PhoneError`/`NoPhoneError` to `error: ...` + exit 1 |
| `src/iring/clip.py` | `parse_time`, `resolve_clip(start, end) -> (start_s, duration_s)`. 30s default, 40s max (iOS limit) |
| `src/iring/audio.py` | Shells out to `yt-dlp` and `ffmpeg`/`ffprobe` (the system binaries, not Python packages, so `brew upgrade yt-dlp` keeps downloads working) |
| `src/iring/tones.py` | Pure functions on the phone's ringtone list: `add_tone`, `find_tones`, `remove_tones`, `clean_title`. All tested, never mutate input |
| `src/iring/phone.py` | pymobiledevice3 AFC access: `connect()` context manager → `Phone`; `push_ringtone`, `read_library`, `delete_ringtones` |
| `tests/` | pytest: clip parsing, tone-list editing, CLI via `typer.testing.CliRunner` with phone functions monkeypatched |
| `docs/*.tape`, `docs/*.gif` | vhs scripts and recorded README GIFs (`make gifs`, needs vhs and a connected phone) |

## Pipeline

1. `yt-dlp --no-playlist -f bestaudio` (playlist links → that single video). Prints title and final file path.
2. `ffmpeg -ss START -i src -t DUR -af afade=out (last 1s) -ar 44100 -c:a aac -b:a 256k -f ipod out.m4r`.
   Encode straight from the original stream (opus/m4a) to avoid a double lossy step. Length is read back with ffprobe;
   an empty result means `--start` was past the end of the track.
3. Push over USB (below). If no phone is connected the `.m4r` is kept and the exact push command is printed.

## How pushing to the iPhone works (verified on iPhone 16, iOS 27.0.1)

Uses AFC (`com.apple.afc`) over usbmux/lockdown. It works on any iOS without Developer Mode, a tunnel or a jailbreak.
The phone only needs to be unlocked and to trust the Mac.

- Tone files: `/iTunes_Control/Ringtones/XXXX.m4r` (4 random uppercase letters; avoid names already in the folder).
- List that Settings reads: `/iTunes_Control/iTunes/Ringtones.plist`, a **binary** plist (write it back as binary):
  ```
  {"Ringtones": {"XXXX.m4r": {"Name": str, "GUID": 16 uppercase hex, "PID": random int64 > 0,
                              "Protected Content": False, "Total Time": ms}}}
  ```
- Copy the file plus add the entry, and the tone shows up in Settings → Sounds & Haptics → Ringtone and plays. No respring needed.
  Finder uses the same mechanism.
- Same name pushed again → the old entry is removed and its file deleted (no duplicates).
- Before every write, the original plist is backed up to `~/Library/Application Support/iring/backups/Ringtones-<timestamp>.plist`.
- Built-in Apple tones aren't in this plist, so `--delete` can't touch them.

### pymobiledevice3 API notes

The library is **async** (v11+); older sync examples online are stale. Verify signatures in the installed source before use.
The `pymobiledevice3-device-operator` skill is installed; read its `references/python-scripting.md` first.

```python
lockdown = await create_using_usbmux()           # raises NoDeviceConnectedError / ConnectionFailedToUsbmuxdError / PairingError
async with lockdown, AfcService(lockdown) as afc:
    await afc.exists(p); await afc.get_file_contents(p); await afc.set_file_contents(p, data)
    await afc.listdir(dir)  # bare names, no . or ..
    await afc.rm(p); await afc.makedirs(p)
    lockdown.short_info["DeviceName"]
```

The `pymobiledevice3` CLI is also installed globally (`~/.local/bin`) and in `.venv/bin` for manual poking, e.g.
`pymobiledevice3 afc ls /iTunes_Control/Ringtones`.

## Researched and rejected: setting the *current* ringtone

Not possible through any supported, non-developer channel. Investigated 2026-11-01:
- AFC only reaches the media area (`/var/mobile/Media`); the selected-ringtone preference lives in system preferences outside it.
- Lockdown domains `com.apple.springboard`, `com.apple.preferences.sounds` and `com.apple.ToneLibrary` read back as `{}`.
- pymobiledevice3's CoreDevice `ConfigurationService` only has appearance and accessibility knobs; the file service only covers
  app containers, temp and crash logs. Both need Developer Mode, which is off on the user's phone.
- Possible but rejected: (1) edit a full backup and restore it, which risks losing data and is slow; (2) Developer Mode plus a
  signed WebDriverAgent to tap through Settings, which needs Xcode, re-signing every 7 days with a free Apple ID, and breaks on UI changes.
Decision: users set it in Settings themselves; iring prints where to find the tone after each push.

## Development

```sh
make sync      # uv sync
make check     # ruff check + ruff format --check + pytest (CI runs only the ruff part)
make format    # ruff --fix + format
make install   # uv tool install --editable --reinstall .  → `iring` on PATH (~/.local/bin)
make gifs      # re-record README GIFs (pushes, then deletes, a "My Heart" tone on the phone)
```

- Python 3.15 locally (`.python-version`), `requires-python >=3.12`. Managed with **uv**. Don't use pip.
- Ruff: line length 120, rules `E F W I B UP`. CI is `.github/workflows/lint.yml` (push to `master`, PRs, manual dispatch) using `astral-sh/ruff-action`.
- Tests stay offline: monkeypatch `cli.read_library` / `cli.delete_ringtones` / `cli.download` rather than touching a device.
  Do real-device checks by hand with a throwaway tone name, then delete it.
- License: GPL-3.0-or-later (required in practice because pymobiledevice3 is GPL-3.0). Keep `THIRD_PARTY_NOTICES.md` updated when adding dependencies.

## Gotchas hit while building

- **yt-dlp goes stale fast.** An old version only got the 360p video stream ("page needs to be reloaded" / SSAP warnings). Fix: `brew upgrade yt-dlp`.
- **Rich markup eats square brackets** in help text: `"[default: x]"` vanishes. Use Typer's `show_default="x"` instead.
- Rich auto-highlights numbers and words like `ringtone(s)`; pass `highlight=False` for plain messages.
- **`sed` on this Mac is GNU sed** (coreutils aliases such as gsed, gls). `sed -i ''` breaks; use `sed -i`, or better, the Edit tool.

## Repo conventions

- Default branch is `master`.
- No "Generated with Claude Code" lines or Claude `Co-Authored-By` trailers in commits, PRs or files.
