# Third-party notices

iring is licensed under the [GNU General Public License v3.0 or later](LICENSE).
It builds on the following projects, each under its own license.

## Python dependencies

These are installed from PyPI when you install iring.

| Project | License | Used for |
|---|---|---|
| [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) | GPL-3.0-or-later | Talking to the iPhone over USB (AFC file transfer) |
| [Typer](https://github.com/fastapi/typer) | MIT | Command-line interface |
| [Rich](https://github.com/Textualize/rich) | MIT | Terminal output: spinners, tables, colors |

Their own dependencies are listed in `uv.lock`, and each one ships its license in its installed package metadata.

## External tools

iring runs these as separate programs. They are not bundled with or distributed alongside iring;
you install them yourself (for example with Homebrew).

| Tool | License | Used for |
|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense (public domain) | Downloading audio from YouTube |
| [FFmpeg](https://ffmpeg.org) | LGPL-2.1-or-later, or GPL depending on the build (Homebrew's build is GPL-3.0-or-later) | Trimming and encoding the ringtone |

## Content

iring doesn't include any audio. You're responsible for having the rights to whatever you turn into a ringtone.
The README demos (which contain no audio) were recorded using a track from [NCS](https://ncs.io) (NoCopyrightSounds).
