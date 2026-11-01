<div align="center">

# 🔔 iring

**Paste a YouTube link. Get a ringtone on your iPhone.**

No iTunes. No GarageBand. No dragging files around in Finder.

[![Lint](https://github.com/sayan01/iring/actions/workflows/lint.yml/badge.svg)](https://github.com/sayan01/iring/actions/workflows/lint.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![macOS](https://img.shields.io/badge/macOS-000000?logo=apple&logoColor=white)](#requirements)
[![iOS](https://img.shields.io/badge/iOS-tested%20on%2027-000000?logo=ios&logoColor=white)](#how-it-works)

<img src="docs/demo.gif" alt="iring turning a YouTube link into a ringtone on an iPhone" width="820">

</div>

---

## ✨ What it does

Making a custom iPhone ringtone normally means downloading audio, trimming it in an editor,
converting it to Apple's `.m4r` format, then plugging in your phone and dragging the file into Finder.

**iring does all of that in one command:**

| | Step | What happens |
|---|---|---|
| ⬇️ | **Download** | Grabs the best-quality audio from the YouTube video (just the video, even if the link is part of a playlist) |
| ✂️ | **Trim** | Cuts the part you want: the first 30 seconds by default, or any range up to 40s, with a smooth fade-out |
| 🎵 | **Convert** | Encodes high-quality AAC in the `.m4r` format iPhones use for ringtones |
| 📱 | **Install** | Copies it straight onto your USB-connected iPhone, where it shows up in **Settings → Sounds & Haptics → Ringtone** |

It can also **list** and **delete** your custom ringtones, which the iPhone itself can't do.

## 🚀 Quick start

```sh
# 1. Tools iring uses for downloading and converting
brew install yt-dlp ffmpeg

# 2. Install iring (needs uv: https://docs.astral.sh/uv/)
uv tool install git+https://github.com/sayan01/iring

# 3. Plug in your iPhone, unlock it, and go
iring "https://youtu.be/jK2aIUmmdP4"
```

> [!TIP]
> The first time you connect, your iPhone will ask whether to **Trust This Computer**. Tap Trust.

## 🎛️ Usage

```sh
iring "<youtube url>"                         # first 30 seconds
iring "<youtube url>" --start 1:05            # 30 seconds starting at 1:05
iring "<youtube url>" -s 1:05 -e 1:35         # exactly 1:05 → 1:35 (max 40s)
iring "<youtube url>" --name "Wake Up"        # choose the name shown in Settings
iring "<youtube url>" --no-push               # just make the .m4r file
iring ~/Music/iring/Song.m4r                  # put an existing .m4r on the phone
```

Times can be written as `90`, `1:05` or `1:02:03`.

### Manage what's on your phone

```sh
iring --list                                  # show your custom ringtones
iring --delete heroes                         # delete tones whose name contains "heroes"
```

<img src="docs/delete.gif" alt="Deleting a ringtone with iring --delete" width="820">

`--delete` always shows what matched and asks before removing anything (add `-y` to skip the question).
Apple's built-in ringtones are never touched.

### Good to know

- 💾 Every ringtone is also saved on your Mac in `~/Music/iring`.
- 🔁 Adding a ringtone with a name that's already on the phone **replaces** it instead of making a duplicate.
- 🛟 Before every change, the phone's ringtone list is backed up to `~/Library/Application Support/iring/backups`.
- 🔌 No phone plugged in? You still get the `.m4r`, plus the exact command to push it later.
- ⌨️ `iring --install-completion` turns on tab completion in your shell.

## 🔍 How it works

```mermaid
flowchart LR
    A["🔗 YouTube URL"] -->|yt-dlp| B["🎧 best audio stream"]
    B -->|"ffmpeg: trim + fade + AAC"| C["🎵 Song.m4r"]
    C -->|"pymobiledevice3 (USB)"| D["📱 iPhone"]
    D --> E["⚙️ Settings → Ringtone"]
```

iPhones keep custom ringtones in an `iTunes_Control/Ringtones` folder, plus a list (`Ringtones.plist`)
that tells Settings which tones exist and what they're called. Finder uses the same mechanism when you drag a
ringtone onto your phone.

iring talks to the phone over USB using [pymobiledevice3](https://github.com/doronz88/pymobiledevice3)'s
file-transfer service (AFC). It copies the `.m4r` into that folder and adds an entry to the list. No jailbreak,
no developer mode, no Apple ID.

Tested on an **iPhone 16 running iOS 27.0.1**.

## 📋 Requirements

- A Mac with [Homebrew](https://brew.sh) and [uv](https://docs.astral.sh/uv/)
- `yt-dlp` and `ffmpeg`. Keep yt-dlp current (`brew upgrade yt-dlp`), since YouTube changes often.
- An iPhone connected by USB, unlocked, and set to trust the Mac

## 🛠️ Development

```sh
git clone git@github.com:sayan01/iring.git && cd iring
make sync        # install dependencies
make install     # put your working copy on PATH as `iring`
make check       # lint + tests
make format      # auto-fix and format
make gifs        # re-record the README GIFs (needs vhs and a connected iPhone)
make help        # list everything
```

## ⚖️ A note on content

Only make ringtones from audio you have the right to use, such as royalty-free music like
[NCS](https://ncs.io) or your own uploads. iring uses Apple's file-transfer interface, which isn't an
officially supported way to install ringtones. Your existing ringtones are backed up before every change.
