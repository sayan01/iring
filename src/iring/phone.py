"""Managing ringtones on a USB-connected iPhone over AFC."""

import plistlib
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from pymobiledevice3.exceptions import (
    ConnectionFailedToUsbmuxdError,
    NoDeviceConnectedError,
    PairingError,
)
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.afc import AfcService

from iring.tones import add_tone, empty_library, remove_tones

RINGTONES_DIR = "/iTunes_Control/Ringtones"
LIBRARY_PLIST = "/iTunes_Control/iTunes/Ringtones.plist"


class NoPhoneError(RuntimeError):
    pass


class PhoneError(RuntimeError):
    pass


class Phone:
    def __init__(self, afc: AfcService, name: str, raw_library: bytes | None, backup_dir: Path):
        self.afc = afc
        self.name = name
        self.library = plistlib.loads(raw_library) if raw_library else empty_library()
        self._raw_library = raw_library
        self._backup_dir = backup_dir

    async def save_library(self, library: dict) -> None:
        """Write the ringtone list back, keeping a copy of the previous one in the backup dir."""
        if self._raw_library is not None:
            self._backup_dir.mkdir(parents=True, exist_ok=True)
            (self._backup_dir / f"Ringtones-{datetime.now():%Y%m%d-%H%M%S}.plist").write_bytes(self._raw_library)
        await self.afc.set_file_contents(LIBRARY_PLIST, plistlib.dumps(library, fmt=plistlib.FMT_BINARY))
        self.library = library

    async def delete_files(self, fnames: list[str]) -> None:
        existing = set(await self.afc.listdir(RINGTONES_DIR))
        for fname in fnames:
            if fname in existing:
                await self.afc.rm(f"{RINGTONES_DIR}/{fname}")


@asynccontextmanager
async def connect(backup_dir: Path):
    try:
        lockdown = await create_using_usbmux()
    except (NoDeviceConnectedError, ConnectionFailedToUsbmuxdError):
        raise NoPhoneError("no iPhone connected over USB") from None
    except PairingError as e:
        raise PhoneError(f"unlock the iPhone and tap 'Trust' if asked, then retry ({type(e).__name__})") from None

    async with lockdown, AfcService(lockdown) as afc:
        raw = await afc.get_file_contents(LIBRARY_PLIST) if await afc.exists(LIBRARY_PLIST) else None
        yield Phone(afc, lockdown.short_info.get("DeviceName", "iPhone"), raw, backup_dir)


async def push_ringtone(m4r: Path, name: str, total_ms: int, backup_dir: Path) -> tuple[str, list[str]]:
    """Upload `m4r` and list it as `name`. Returns (device name, replaced tone files)."""
    async with connect(backup_dir) as phone:
        if not await phone.afc.exists(RINGTONES_DIR):
            await phone.afc.makedirs(RINGTONES_DIR)
        existing = set(await phone.afc.listdir(RINGTONES_DIR))

        updated, fname, replaced = add_tone(phone.library, name, total_ms, existing)
        await phone.afc.set_file_contents(f"{RINGTONES_DIR}/{fname}", m4r.read_bytes())
        await phone.save_library(updated)
        await phone.delete_files(replaced)
        return phone.name, replaced


async def read_library(backup_dir: Path) -> tuple[str, dict]:
    async with connect(backup_dir) as phone:
        return phone.name, phone.library


async def delete_ringtones(fnames: list[str], backup_dir: Path) -> str:
    async with connect(backup_dir) as phone:
        await phone.save_library(remove_tones(phone.library, fnames))
        await phone.delete_files(fnames)
        return phone.name
