# sg0hann Crosshair Color Lab

Windows click-through crosshair overlay for Creative Destruction. **v1.0.2 adds automatic build reticle switching:** pressing a build hotkey (F/X/C/H/F4) while the game is focused temporarily displays the circular Pickaxe-style reticle; E/Esc or selecting a weapon slot 1–5 returns to the selected shotgun/AR/pickaxe reticle. This does not overwrite selected weapon colors. **v1.0.1 added scoped/ADS behavior:** by default the colored overlay hides while right mouse button is held in-game, then reappears on release. Choose **Toggle** under Right-click aim if the game is set to toggle ADS instead of hold. This avoids leaving a stationary crosshair on top of the scope or zoomed AR view. Includes shotgun, AR/sniper and pickaxe reticles; editable colors, size, offsets and weapon-slot mappings.

The overlay does not edit game files or bypass anti-cheat. The native white reticle remains underneath.

The app checks this repository's latest GitHub Release on startup and via the **Check for Updates** button. An available update is offered in a popup; with approval, the app downloads and verifies the installer and runs it. Settings persist in `%APPDATA%\sg0hann-crosshair\settings.json`.

Download the latest Windows `.exe` from the [Releases](https://github.com/samimustafaa/crosshair-change-cd/releases/latest) page after the Windows build completes.

The workflow runs on Windows and uses PyInstaller plus Inno Setup. Each new app version should increase the `VERSION` constant in `sg0hann_crosshair.py`. A new push to `main` publishes the corresponding release if that version hasn't already been released.

Hotkeys: **F6** cycle mode, **F7** toggle overlay, **F8** settings, **1–5** select mapped weapon-slot mode while the game is focused.

This is an external overlay, not actual recoloring of the game's HUD texture; use borderless-windowed mode if the game hides external overlays.

## Scope / right-click ADS (v1.0.1)

Under **Overlay Options**, turn on **Hide crosshair when aiming / scoped** (enabled by default). Set **Right-click aim** to **Hold** (default) or **Toggle**, to match the game's aim configuration. The app uses right-mouse input while Creative Destruction is focused; it does not read the game's scope state. If your aim key is changed from RMB, this feature won't automatically follow it. This prevents the colored overlay from lingering at the center of zoomed AR views or inside sniper scopes.

## Build mode reticle (v1.0.2)

The **Circle crosshair when building** option is enabled by default in Overlay Options. When Creative Destruction is focused:

- Press **F** (wall), **X** (floor), **C** (stairs), **H**, or **F4** to show the **Pickaxe** circular crosshair, using the color configured for Pickaxe.
- Switching between build parts retains the circular crosshair.
- Press **E** (Cancel), **Esc**, or a **1–5** weapon-slot key to restore the previous weapon reticle (or the selected weapon-slot's style).
- During inferred build mode, the ADS hide feature will not hide the circular reticle on a right-click.
- You can turn **Circle crosshair when building** off if your game's controls differ.

**Limitations:** This version follows default keyboard hotkeys, not internal game build-mode state; mouse-only build selections, custom keybinds, exiting build mode via an untracked control, or refocusing the game in build mode may leave the external overlay temporarily out of sync. Use E/Esc or select a weapon slot to resync. It does not alter the game's native white reticle.
