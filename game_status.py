"""Read-only Creative Destruction process detection, independent of focus.

The status badge is based on an EXE process being present; overlay drawing still
requires the game's window to be focused. No injection or memory access.
"""
from __future__ import annotations

def identify_game_process(info: dict) -> str | None:
    name = str(info.get("name") or "").strip().lower()
    path = str(info.get("exe") or "").replace("/", "\\").lower()
    if name in ("creative destruction.exe", "cdrevive.exe"):
        return name
    if name == "client.exe":
        # The game uses client.exe. Prefer a verified installation directory.
        # Process path can be unavailable to a standard user, so don't reject
        # an exact client.exe match merely because the path is inaccessible.
        if not path or "creative destruction" in path or "cdrevive" in path or "cd revive" in path:
            return name
    return None


def detect_running_game(processes=None) -> str | None:
    """Return matched EXE or None. Can accept mocked process info in tests."""
    if processes is None:
        try:
            import psutil
            processes = psutil.process_iter(attrs=("name", "exe"), ad_value=None)
        except Exception:
            return None
    for process in processes:
        try:
            info = process if isinstance(process, dict) else process.info
            found = identify_game_process(info)
            if found:
                return found
        except Exception:
            # Process may exit while enumerating or deny access.
            continue
    return None
