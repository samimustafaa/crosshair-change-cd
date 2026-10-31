# sg0hann Crosshair Color Lab

Windows click-through crosshair overlay for Creative Destruction. **v1.0.1 adds scoped/ADS behavior:** by default the colored overlay hides while right mouse button is held in-game, then reappears on release. Choose **Toggle** under Right-click aim if the game is set to toggle ADS instead of hold. This avoids leaving a stationary crosshair on top of the scope or zoomed AR view. Includes shotgun, AR/sniper and pickaxe reticles; editable colors, size, offsets and weapon-slot mappings.

The overlay does not edit game files or bypass anti-cheat. The native white reticle remains underneath.

The app checks this repository's latest GitHub Release on startup and via the **Check for Updates** button. An available update is offered in a popup; with approval, the app downloads and verifies the installer and runs it. Settings persist in `%APPDATA%\sg0hann-crosshair\settings.json`.

Download the latest Windows `.exe` from the [Releases](https://github.com/samimustafaa/crosshair-change-cd/releases/latest) page after the Windows build completes.

The workflow runs on Windows and uses PyInstaller plus Inno Setup. Each new app version should increase the `VERSION` constant in `sg0hann_crosshair.py`. A new push to `main` publishes the corresponding release if that version hasn't already been released.

Hotkeys: **F6** cycle mode, **F7** toggle overlay, **F8** settings, **1–5** select mapped weapon-slot mode while the game is focused.

This is an external overlay, not actual recoloring of the game's HUD texture; use borderless-windowed mode if the game hides external overlays.

## Scope / right-click ADS (v1.0.1)

Under **Overlay Options**, turn on **Hide crosshair when aiming / scoped** (enabled by default). Set **Right-click aim** to **Hold** (default) or **Toggle**, to match the game's aim configuration. The app uses right-mouse input while Creative Destruction is focused; it does not read the game's scope state. If your aim key is changed from RMB, this feature won't automatically follow it. This prevents the colored overlay from lingering at the center of zoomed AR views or inside sniper scopes.

