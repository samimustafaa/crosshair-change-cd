# sg0hann Crosshair Color Lab

Windows click-through crosshair overlay for Creative Destruction. Includes shotgun, AR/sniper and pickaxe reticles; editable colors, size, offsets and weapon-slot mappings.

The overlay does not edit game files or bypass anti-cheat. The native white reticle remains underneath.

The app checks this repository's latest GitHub Release on startup and via the **Check for Updates** button. An available update is offered in a popup; with approval, the app downloads and verifies the installer and runs it. Settings persist in `%APPDATA%\sg0hann-crosshair\settings.json`.

Download the latest Windows `.exe` from the [Releases](https://github.com/samimustafaa/crosshair-change-cd/releases/latest) page after the Windows build completes.

The workflow runs on Windows and uses PyInstaller plus Inno Setup. Each new app version should increase the `VERSION` constant in `sg0hann_crosshair.py`. A new push to `main` publishes the corresponding release if that version hasn't already been released.

Hotkeys: **F6** cycle mode, **F7** toggle overlay, **F8** settings, **1–5** select mapped weapon-slot mode while the game is focused.

This is an external overlay, not actual recoloring of the game's HUD texture; use borderless-windowed mode if the game hides external overlays.
