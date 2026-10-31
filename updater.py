"""GitHub Releases update support for sg0hann Crosshair Color Lab.

Only downloads from the fixed public repository. The app asks before installing.
No code injection, Defender bypass, or automatic execution without consent.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

OWNER_REPO = "samimustafaa/crosshair-change-cd"
API = f"https://api.github.com/repos/{OWNER_REPO}/releases/latest"
INSTALLER_NAME = "sg0hann-Crosshair-Setup.exe"
HASHES_NAME = "SHA256SUMS.txt"
MAX_INSTALLER_BYTES = 160 * 1024 * 1024


def _get(url: str, max_bytes: int) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "sg0hann-Crosshair-Updater/1.0",
        "Accept": "application/vnd.github+json" if url == API else "application/octet-stream",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("Downloaded file exceeds size limit.")
        return data


def _version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value.strip())
    if not match:
        raise ValueError("Release has an unsupported version tag.")
    return tuple(map(int, match.groups()))


def find_update(current_version: str) -> dict | None:
    try:
        release = json.loads(_get(API, 1024 * 1024))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None  # No releases published yet.
        raise
    version = release.get("tag_name", "")
    if _version(version) <= _version(current_version):
        return None
    assets = {a.get("name"): a.get("browser_download_url")
              for a in release.get("assets", []) if isinstance(a, dict)}
    if not assets.get(INSTALLER_NAME) or not assets.get(HASHES_NAME):
        raise ValueError("The newest release is missing its installer or SHA256 checksum.")
    for url in (assets[INSTALLER_NAME], assets[HASHES_NAME]):
        if not isinstance(url, str) or not url.startswith(
                f"https://github.com/{OWNER_REPO}/releases/download/"):
            raise ValueError("Unexpected release asset URL.")
    return {
        "version": version.lstrip("v"),
        "notes": release.get("body") or "",
        "installer_url": assets[INSTALLER_NAME],
        "hashes_url": assets[HASHES_NAME],
        "page_url": release.get("html_url") or f"https://github.com/{OWNER_REPO}/releases/latest",
    }


def download_verified_installer(release: dict) -> Path:
    hashes = _get(release["hashes_url"], 20_000).decode("utf-8")
    expected = None
    for line in hashes.splitlines():
        match = re.fullmatch(r"([a-fA-F0-9]{64})\s+\*?(.+)", line.strip())
        if match and match.group(2) == INSTALLER_NAME:
            expected = match.group(1).lower()
            break
    if expected is None:
        raise ValueError("Installer checksum was not found in SHA256SUMS.txt.")

    # Downloading in a worker avoids blocking the UI.
    content = _get(release["installer_url"], MAX_INSTALLER_BYTES)
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError("The downloaded installer failed SHA256 verification.")
    folder = Path(tempfile.mkdtemp(prefix="sg0hann-update-"))
    target = folder / INSTALLER_NAME
    target.write_bytes(content)
    return target


def launch_installer(installer: Path) -> None:
    if sys.platform != "win32":
        raise RuntimeError("Updating requires Windows.")
    # The installer itself starts the fully installed app after copying all DLLs.
    # Never let Restart Manager relaunch the old EXE mid-install.
    subprocess.Popen(
        [str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
         "/CLOSEAPPLICATIONS", "/NORESTARTAPPLICATIONS"],
        creationflags=0x00000008,  # DETACHED_PROCESS
        close_fds=True,
    )
