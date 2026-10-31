# sg0hann Crosshair Color Lab

Windows click-through crosshair overlay for Creative Destruction. **v1.0.3 redesign:** wider dark settings window with sidebar navigation, independent Crosshair / Gameplay / Updates pages, always-visible live reticle preview, per-mode color picker and size/thickness/offset sliders, visual focus states, and scrolling panels on smaller monitors. **v1.0.2 adds automatic build reticle switching:** pressing a build hotkey (F/X/C/H/F4) while the game is focused temporarily displays the circular Pickaxe-style reticle; E/Esc or selecting a weapon slot 1–5 returns to the selected shotgun/AR/pickaxe reticle. This does not overwrite selected weapon colors. **v1.0.1 added scoped/ADS behavior:** by default the colored overlay hides while right mouse button is held in-game, then reappears on release. Choose **Toggle** under Right-click aim if the game is set to toggle ADS instead of hold. This avoids leaving a stationary crosshair on top of the scope or zoomed AR view. Includes shotgun, AR/sniper and pickaxe reticles; editable colors, size, offsets and weapon-slot mappings.

The overlay does not edit game files or bypass anti-cheat. The native white reticle remains underneath.

The app checks this repository's latest GitHub Release on startup and via the **Check for Updates** button. An available update is offered in a popup; with approval, the app downloads and verifies the installer and runs it. Settings persist in `%APPDATA%\sg0hann-crosshair\settings.json`.

Download the **installer** from [Releases](https://github.com/samimustafaa/crosshair-change-cd/releases/latest). The portable alternative is now a ZIP containing both the executable and its `_internal` Python libraries: extract **all files together** before launching. The EXE alone is no longer a portable executable.

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

## Interface redesign (v1.0.3)

The settings window uses a clean dark wide layout (up to 1180×772), with three left navigation pages:

- **Crosshair:** change shotgun, AR/sniper, and pickaxe reticle colors; select the active weapon; adjust position, size and thickness; see live-preview changes immediately.
- **Gameplay:** enable/disable overlay, hide during ADS, automatically switch to the circular build reticle, configure hold/toggle ADS, and map slots 1–5.
- **Updates:** manually check GitHub Releases and install an update after approval. An automatic check still runs at startup.

All gameplay behavior from v1.0.2 remains. The window is non-resizable and centered. Scroll the left settings panel when space is limited; the preview stays visible. Press **F8** to open/hide settings while playing.

## Windows Python DLL startup fix (v1.0.4)

The previous one-file EXE extracted the Python runtime to a random `%TEMP%\\_MEI...` directory on every launch. A missing, quarantined, or inaccessible DLL in that temporary folder could show **Failed to load Python DLL python312.dll**. v1.0.4 builds with **PyInstaller --onedir** instead. Inno Setup installs `sg0hann-Crosshair.exe` and `_internal\\python312.dll` into the same persistent application directory. The Windows CI build checks the DLL exists and runs the packaged application with `--self-test` to verify Python/Tk startup before uploading the installer.

To recover from an existing startup error:
1. Exit sg0hann Crosshair Color Lab completely (end it in Task Manager if necessary).
2. Download and run the **v1.0.4 installer** directly from GitHub Releases (do not run the old standalone EXE).
3. You can install over the existing version; your saved settings live separately in `%APPDATA%\\sg0hann-crosshair\\settings.json` and should remain intact.
4. If using the portable package, extract the entire ZIP with the `_internal` folder present alongside the EXE. Do not move just the EXE elsewhere.
5. If a DLL still fails to load after a full install, check Windows Security Protection History for quarantined runtime files and the official Microsoft Visual C++ Redistributable x64 prerequisites. Do not disable antivirus or add broad exclusions.

For silent in-app updates, the installer closes the existing application, installs all files, and launches the updated copy after installation; it avoids restarting an old version before copying the new runtime.

## Native Lab — experimental only (v1.0.5)

The new **Native Lab** sidebar page opens a user-selected local `ui1.npk`, previews four indexed visual candidates (white ring, three-arc ring, alternate ring, segmented ring), recolors white pixels into user-chosen colors, and exports PNG images. An optional explicit-consent button produces a **separate experimental NPK copy** and reads its modified asset back to confirm archive consistency. The original archive and game installation are never modified by the app.

**Important:** The candidate file IDs are not proven to control combat crosshairs, and this archive's two unknown hash fields are not recalculated. In-game use and archive integrity compatibility are **unverified**. Do not replace your game files or use a modified NPK online based only on this copy. No anti-cheat bypass is attempted. The previously working external overlay is still the default functional crosshair customization method.

## v1.0.7 — Native Lab feedback and game status

- In **Native Lab**, browse to the **complete extracted** `ui1.npk`, or paste the path and press **Enter**; selection automatically validates the archive. A visible `ARCHIVE LOADED` or `ARCHIVE NOT LOADED` status appears beside the input, including file size, indexed resources and candidate ID matches. The currently selected image automatically previews; preview errors are visible near the archive input. **Loading a file does not apply any crosshair changes**—the original native reticle IDs are still unverified.
- In the top bar, `GAME OPENED` appears in green if Creative Destruction's process (typically `client.exe`) is running, even when the app is in the foreground. `GAME CLOSED` appears otherwise. The game overlay still shows only while Creative Destruction has focus when “Show only in Creative Destruction” is enabled.
- Status is checked about every 1.3 seconds using read-only process enumeration. For `client.exe`, the detector prefers Creative Destruction installation paths. If Windows hides a process path, an exact `client.exe` name is used; this may occasionally recognize an unrelated process with that name.

All existing crosshair settings, updating, native preview/export, and experimental copy-only features remain.

## Reactive spread (v1.0.9)

In **Gameplay → Spray & jump tracking**, enable **Reactive crosshair spread** (enabled by default). When Creative Destruction is focused, holding **left mouse button** while using a gun progressively expands the colored reticle and **Space** causes a temporary jump expansion. The reticle gradually returns to normal after releasing the input. Default amounts: 85% spray expansion, 55% jump expansion, 320 ms fire recovery. Sliders adjust both expansion amounts and recovery speed. Use **Preview spray + jump** to see the maximum effect in the UI without having to enter a match.

Sampling is scheduled every **12 milliseconds** (approximately 83 updates per second when the Windows event loop can keep up); no precise latency guarantee. Reading button input is faster and less prone to false visual detections than tracking white HUD pixels against the game world. This is a **predictive approximation**, NOT actual native-game bloom tracking. Input-based spread may not perfectly match the base white crosshair, weapon fire-rate curves, falling, moving, crouching, or custom jump/fire keybinds. It does not read game memory or modify NPK files. Scoped ADS, building and pickaxe do not expand the custom reticle.
