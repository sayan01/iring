# iring

YouTube link → iPhone ringtone, copied straight onto a USB-connected iPhone (no Finder drag-and-drop).

```
iring "<youtube url>"                         # first 30 seconds
iring "<youtube url>" --start 1:05            # 30 seconds from 1:05
iring "<youtube url>" -s 1:05 -e 1:35         # explicit range (max 40s)
iring "<youtube url>" --name "Wake Up"        # name shown in Settings
iring "<youtube url>" --no-push               # only make the .m4r
iring ~/Music/iring/Song.m4r                  # push an existing .m4r
iring --list                                  # custom ringtones on the phone
iring --delete heroes                         # delete tones whose name contains "heroes" (asks first; -y to skip)
```

Ringtones are kept in `~/Music/iring`. Pushing a tone with the same name as one already on the phone replaces it.
Before every change, the phone's ringtone list is backed up to `~/Library/Application Support/iring/backups`.
`iring --install-completion` sets up tab completion for your shell.

## How it works

1. `yt-dlp` downloads the best audio stream (single video, even for playlist links).
2. `ffmpeg` cuts the clip, adds a 1s fade-out and encodes 256k AAC as `.m4r`.
3. `pymobiledevice3` copies it over AFC to `/iTunes_Control/Ringtones/XXXX.m4r` and adds an entry to
   `/iTunes_Control/iTunes/Ringtones.plist`, which is what makes it appear in Settings.
   Tested on iPhone 16, iOS 27.0.1.

## Setup

Needs `yt-dlp` and `ffmpeg` (`brew install yt-dlp ffmpeg`) and [uv](https://docs.astral.sh/uv/).

```
uv tool install --editable .     # puts `iring` on your PATH
uv run pytest                    # tests
```

The iPhone must be unlocked and have trusted this Mac at least once.
