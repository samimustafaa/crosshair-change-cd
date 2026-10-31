"""sg0hann Crosshair Color Lab - Windows click-through overlay, v1.0.1.

No game-file modification, injection, or anti-cheat bypass.
"""
from __future__ import annotations

import ctypes
import json
import os
import queue
import sys
import threading
import tkinter as tk
from ctypes import wintypes
from pathlib import Path
from tkinter import colorchooser, messagebox, ttk

from aim_state import AimTracker, crosshair_visible
from updater import download_verified_installer, find_update, launch_installer

VERSION = "1.0.1"
APP_NAME = "sg0hann Crosshair Color Lab"
TRANSPARENT = "#010203"
BG, PANEL, CARD = "#111419", "#1B2028", "#242B35"
TEXT, MUTED, ACCENT = "#EFF2F6", "#9DA8B6", "#7FB5FF"
MODES = ("Shotgun", "AR / Sniper", "Pickaxe")
DEFAULTS = {
    "colors": {"Shotgun": "#00E7FF", "AR / Sniper": "#B2FF59", "Pickaxe": "#FFCC42"},
    "active_mode": "AR / Sniper",
    "slot_mapping": {"1": "Pickaxe", "2": "AR / Sniper", "3": "Shotgun",
                     "4": "AR / Sniper", "5": "AR / Sniper"},
    "offset_x": 0, "offset_y": 0, "size": 100, "thickness": 3,
    "only_in_game": True, "overlay_enabled": True,
    "hide_while_aiming": True, "aim_input": "Hold",
}

if sys.platform == "win32":
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                    wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def settings_path() -> Path:
    return Path(os.environ.get("APPDATA", str(Path.home()))) / "sg0hann-crosshair" / "settings.json"


def config_load() -> dict:
    data = json.loads(json.dumps(DEFAULTS))
    try:
        raw = json.loads(settings_path().read_text(encoding="utf-8"))
        for key in ("active_mode", "offset_x", "offset_y", "size", "thickness",
                    "only_in_game", "overlay_enabled", "hide_while_aiming", "aim_input"):
            if key in raw:
                data[key] = raw[key]
        for mode in MODES:
            candidate = raw.get("colors", {}).get(mode)
            if (isinstance(candidate, str) and len(candidate) == 7
                    and candidate.startswith("#")
                    and all(ch in "0123456789abcdefABCDEF" for ch in candidate[1:])):
                data["colors"][mode] = candidate
        for number in data["slot_mapping"]:
            mode = raw.get("slot_mapping", {}).get(number)
            if mode in MODES:
                data["slot_mapping"][number] = mode
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    if data["active_mode"] not in MODES:
        data["active_mode"] = "AR / Sniper"
    for key, lo, hi in (("offset_x", -500, 500), ("offset_y", -500, 500),
                        ("size", 50, 200), ("thickness", 2, 8)):
        try:
            data[key] = max(lo, min(hi, int(data[key])))
        except (ValueError, TypeError):
            data[key] = DEFAULTS[key]
    data["only_in_game"] = bool(data["only_in_game"])
    data["overlay_enabled"] = bool(data["overlay_enabled"])
    data["hide_while_aiming"] = bool(data["hide_while_aiming"])
    if data["aim_input"] not in ("Hold", "Toggle"):
        data["aim_input"] = "Hold"
    return data


def config_save(data: dict):
    try:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def game_focused() -> bool:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
    count = user32.GetWindowTextLengthW(hwnd)
    title_buf = ctypes.create_unicode_buffer(count + 1)
    user32.GetWindowTextW(hwnd, title_buf, count + 1)
    title = title_buf.value.lower()
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    name = ""
    if pid.value:
        process = kernel32.OpenProcess(0x1000, False, pid.value)
        if process:
            try:
                length = wintypes.DWORD(1024)
                path_buf = ctypes.create_unicode_buffer(1024)
                if kernel32.QueryFullProcessImageNameW(process, 0, path_buf, ctypes.byref(length)):
                    name = os.path.basename(path_buf.value).lower()
            finally:
                kernel32.CloseHandle(process)
    return (name in ("client.exe", "creative destruction.exe", "cdrevive.exe")
            or "creative destruction" in title or "cd revive" in title)


def draw_reticle(canvas, x, y, mode, color, scale, line_width, tag="reticle"):
    radius = 34 * scale
    dot = max(1.5, 1.9 * scale)
    if mode == "Shotgun":
        for start in (55, 145, 235, 325):
            canvas.create_arc(x-radius, y-radius, x+radius, y+radius,
                              start=start, extent=70, style=tk.ARC,
                              outline=color, width=line_width, tags=(tag,))
    elif mode == "Pickaxe":
        canvas.create_oval(x-radius, y-radius, x+radius, y+radius,
                           outline=color, width=line_width, tags=(tag,))
    else:
        near, far = 18*scale, 32*scale
        for x1, y1, x2, y2 in (
            (x-far, y, x-near, y), (x+near, y, x+far, y),
            (x, y-far, x, y-near), (x, y+near, x, y+far),
        ):
            canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width,
                               capstyle=tk.ROUND, tags=(tag,))
    canvas.create_oval(x-dot, y-dot, x+dot, y+dot,
                       fill=color, outline=color, tags=(tag,))


class CrosshairApp:
    KEY_CODES = {"1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34, "5": 0x35,
                 "F6": 0x75, "F7": 0x76, "F8": 0x77}

    def __init__(self):
        self.cfg = config_load()
        self.down = {key: False for key in self.KEY_CODES}
        self.in_game = False
        self.aim_tracker = AimTracker()
        self.aim_active = False
        self.previous_draw = None
        self.save_timer = None
        self.update_busy = False
        self.events = queue.Queue()

        self.root = tk.Tk()
        self.root.title("sg0hann Overlay")
        self.root.configure(bg=TRANSPARENT)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", TRANSPARENT)
        self.sw, self.sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{self.sw}x{self.sh}+0+0")
        self.canvas = tk.Canvas(self.root, bg=TRANSPARENT, highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.root.update_idletasks()
        self.make_clickthrough()

        self.window = tk.Toplevel(self.root)
        self.window.title(f"{APP_NAME}  v{VERSION}")
        self.window.configure(bg=BG)
        self.window.geometry("760x815")
        self.window.minsize(730, 780)
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        self.window.attributes("-topmost", True)
        self.window.after(1000, lambda: self.window.attributes("-topmost", False))

        self.mode_var = tk.StringVar(value=self.cfg["active_mode"])
        self.overlay_var = tk.BooleanVar(value=self.cfg["overlay_enabled"])
        self.only_game_var = tk.BooleanVar(value=self.cfg["only_in_game"])
        self.hide_ads_var = tk.BooleanVar(value=self.cfg["hide_while_aiming"])
        self.ads_input_var = tk.StringVar(value=self.cfg["aim_input"])
        self.x_var, self.y_var = tk.IntVar(value=self.cfg["offset_x"]), tk.IntVar(value=self.cfg["offset_y"])
        self.size_var = tk.IntVar(value=self.cfg["size"])
        self.thick_var = tk.IntVar(value=self.cfg["thickness"])
        self.slots = {i: tk.StringVar(value=self.cfg["slot_mapping"][i]) for i in "12345"}
        self.status = tk.StringVar(value="Ready - focus Creative Destruction to see the overlay.")
        self.update_status = tk.StringVar(value=f"App version {VERSION} - GitHub Releases")
        self.previews, self.color_buttons = {}, {}
        self.create_ui()
        self.refresh_previews()
        self.poll()
        self.root.after(1600, lambda: self.check_updates(silent=True))
        self.root.after(150, self.poll_updates)

    def make_clickthrough(self):
        hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
        ex_style = user32.GetWindowLongW(hwnd, -20)
        user32.SetWindowLongW(hwnd, -20, ex_style | 0x20 | 0x80000 | 0x80 | 0x08000000)
        user32.SetWindowPos(hwnd, -1, 0, 0, self.sw, self.sh, 0x0010 | 0x0020)

    def label(self, parent, value, size=10, bold=False, color=TEXT, **kwargs):
        return tk.Label(parent, text=value, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def button(self, parent, value, command, bg=CARD):
        return tk.Button(parent, text=value, command=command,
                         bg=bg, fg=TEXT, activebackground="#3C495B",
                         activeforeground="#FFFFFF", bd=0, relief=tk.FLAT,
                         cursor="hand2", font=("Segoe UI", 10, "bold"), padx=12, pady=7)

    def card(self, parent):
        return tk.Frame(parent, bg=PANEL, padx=12, pady=12)

    def create_ui(self):
        header = tk.Frame(self.window, bg=BG, padx=22, pady=16)
        header.pack(fill=tk.X)
        self.label(header, "SG0HANN  /  CROSSHAIR LAB", 10, True, ACCENT).pack(anchor="w")
        self.label(header, "Make your crosshair yours.", 20, True).pack(anchor="w", pady=(4, 0))
        self.label(header, "Lightweight click-through overlay  •  No game file edits",
                   9, color=MUTED).pack(anchor="w", pady=(2, 0))

        bottom = tk.Frame(self.window, bg=BG, padx=20, pady=10)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        columns = tk.Frame(self.window, bg=BG, padx=20)
        columns.pack(fill=tk.BOTH, expand=True)
        left = tk.Frame(columns, bg=BG)
        right = tk.Frame(columns, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        colors = self.card(left)
        colors.pack(fill=tk.X, pady=(0, 12))
        self.label(colors, "CROSSHAIR COLORS", 11, True).pack(anchor="w", pady=(0, 7))
        for mode in MODES:
            row = tk.Frame(colors, bg=PANEL)
            row.pack(fill=tk.X, pady=4)
            preview = tk.Canvas(row, bg=CARD, width=78, height=70, highlightthickness=0)
            preview.pack(side=tk.LEFT)
            self.previews[mode] = preview
            description = tk.Frame(row, bg=PANEL)
            description.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
            self.label(description, mode, 10, True).pack(anchor="w")
            choice = self.button(description, "Choose color", lambda m=mode: self.pick_color(m))
            choice.pack(anchor="w", pady=(4, 0))
            self.color_buttons[mode] = choice

        selection = self.card(left)
        selection.pack(fill=tk.X)
        self.label(selection, "ACTIVE RETICLE", 11, True).pack(anchor="w", pady=(0, 8))
        dropdown = ttk.Combobox(selection, state="readonly", values=MODES,
                                textvariable=self.mode_var)
        dropdown.pack(fill=tk.X)
        dropdown.bind("<<ComboboxSelected>>", lambda _: self.set_mode(self.mode_var.get()))
        self.label(selection, "F6: change style   •   F7: toggle   •   F8: settings",
                   9, color=MUTED, wraplength=310).pack(anchor="w", pady=(9, 0))

        settings = self.card(right)
        settings.pack(fill=tk.X, pady=(0, 12))
        self.label(settings, "OVERLAY OPTIONS", 11, True).pack(anchor="w", pady=(0, 7))
        for title, value in (("Enable crosshair overlay", self.overlay_var),
                             ("Show only while game is focused", self.only_game_var),
                             ("Hide crosshair when aiming / scoped", self.hide_ads_var)):
            tk.Checkbutton(settings, text=title, variable=value,
                           command=self.options_changed, bg=PANEL, fg=TEXT,
                           activebackground=PANEL, activeforeground=TEXT,
                           selectcolor=CARD, font=("Segoe UI", 9)).pack(fill=tk.X, pady=3)
        aim_row = tk.Frame(settings, bg=PANEL)
        aim_row.pack(fill=tk.X, pady=(4, 0))
        self.label(aim_row, "Right-click aim:", 9).pack(side=tk.LEFT)
        ads_dropdown = ttk.Combobox(aim_row, state="readonly", values=("Hold", "Toggle"),
                                     textvariable=self.ads_input_var, width=9)
        ads_dropdown.pack(side=tk.RIGHT)
        ads_dropdown.bind("<<ComboboxSelected>>", lambda _: self.options_changed())
        self.label(settings, "Hold: hide while RMB is down. Toggle: hide until next RMB click.",
                   8, color=MUTED, wraplength=310, justify="left").pack(anchor="w", pady=(5, 0))

        mapping = self.card(right)
        mapping.pack(fill=tk.X, pady=(0, 12))
        self.label(mapping, "WEAPON SLOT SWITCHING", 11, True).pack(anchor="w", pady=(0, 5))
        self.label(mapping, "Press your in-game 1-5 slot keys.",
                   9, color=MUTED).pack(anchor="w", pady=(0, 6))
        for number in "12345":
            row = tk.Frame(mapping, bg=PANEL)
            row.pack(fill=tk.X, pady=2)
            self.label(row, f"Slot {number}", 9).pack(side=tk.LEFT)
            dropdown = ttk.Combobox(row, state="readonly", values=MODES,
                                    textvariable=self.slots[number], width=16)
            dropdown.pack(side=tk.RIGHT)
            dropdown.bind("<<ComboboxSelected>>", lambda _: self.options_changed())

        align = self.card(right)
        align.pack(fill=tk.X)
        self.label(align, "SIZE & ALIGNMENT", 11, True).pack(anchor="w", pady=(0, 8))
        for title, var, lower, upper in (
            ("Horizontal", self.x_var, -500, 500),
            ("Vertical", self.y_var, -500, 500),
            ("Size %", self.size_var, 50, 200),
            ("Thickness", self.thick_var, 2, 8),
        ):
            row = tk.Frame(align, bg=PANEL)
            row.pack(fill=tk.X, pady=3)
            self.label(row, title, 9).pack(side=tk.LEFT)
            inp = tk.Spinbox(row, from_=lower, to=upper, textvariable=var, width=6,
                             bg=CARD, fg=TEXT, buttonbackground=CARD,
                             insertbackground=TEXT, relief=tk.FLAT, justify="center",
                             command=self.options_changed)
            inp.pack(side=tk.RIGHT)
            inp.bind("<KeyRelease>", lambda _: self.options_changed())

        updates = self.card(bottom)
        updates.pack(fill=tk.X, pady=(0, 9))
        self.label(updates, "UPDATES", 11, True).pack(anchor="w")
        self.label(updates, "", 9, color=MUTED,
                   textvariable=self.update_status).pack(side=tk.LEFT, anchor="w")
        self.update_button = self.button(
            updates, "Check for Updates", lambda: self.check_updates(silent=False), bg="#2B5B94")
        self.update_button.pack(side=tk.RIGHT)

        self.label(bottom, "TIP: Borderless-windowed mode works best. The original white crosshair stays underneath.",
                   9, color=MUTED, wraplength=690).pack(anchor="w", pady=(0, 7))
        controls = tk.Frame(bottom, bg=BG)
        controls.pack(fill=tk.X)
        self.button(controls, "Hide settings", self.hide, bg="#2B5B94").pack(side=tk.LEFT)
        self.button(controls, "Reset defaults", self.reset).pack(side=tk.LEFT, padx=8)
        self.button(controls, "Quit", self.quit).pack(side=tk.RIGHT)
        self.label(bottom, "", 9, color=ACCENT,
                   textvariable=self.status).pack(anchor="w", pady=(7, 0))

    def pick_color(self, mode):
        choice = colorchooser.askcolor(color=self.cfg["colors"][mode],
                                       title=f"{mode} color", parent=self.window)
        if choice and choice[1]:
            self.cfg["colors"][mode] = choice[1].upper()
            self.refresh_previews()
            self.render(True)
            self.save_later()

    def refresh_previews(self):
        for mode, canvas in self.previews.items():
            canvas.delete("all")
            color = self.cfg["colors"][mode]
            draw_reticle(canvas, 39, 35, mode, color, .65, 2)
            self.color_buttons[mode].configure(text=color)

    def set_mode(self, mode):
        if mode not in MODES:
            return
        self.cfg["active_mode"] = mode
        self.mode_var.set(mode)
        self.render(True)
        self.save_later()

    @staticmethod
    def bounded(var, fallback, lower, upper):
        try:
            return min(upper, max(lower, int(var.get())))
        except (ValueError, tk.TclError):
            return fallback

    def options_changed(self):
        self.cfg["overlay_enabled"] = self.overlay_var.get()
        self.cfg["only_in_game"] = self.only_game_var.get()
        self.cfg["hide_while_aiming"] = self.hide_ads_var.get()
        selected_aim_mode = self.ads_input_var.get()
        if selected_aim_mode not in ("Hold", "Toggle"):
            selected_aim_mode = "Hold"
        if self.cfg["aim_input"] != selected_aim_mode:
            self.aim_tracker.reset()
            self.aim_active = False
        self.cfg["aim_input"] = selected_aim_mode
        self.cfg["offset_x"] = self.bounded(self.x_var, 0, -500, 500)
        self.cfg["offset_y"] = self.bounded(self.y_var, 0, -500, 500)
        self.cfg["size"] = self.bounded(self.size_var, 100, 50, 200)
        self.cfg["thickness"] = self.bounded(self.thick_var, 3, 2, 8)
        for number, value in self.slots.items():
            if value.get() in MODES:
                self.cfg["slot_mapping"][number] = value.get()
        self.render(True)
        self.save_later()

    def save_later(self):
        if self.save_timer:
            self.window.after_cancel(self.save_timer)
        self.save_timer = self.window.after(450, lambda: config_save(self.cfg))

    def render(self, force=False):
        visible = crosshair_visible(
            self.cfg["overlay_enabled"], self.in_game, self.cfg["only_in_game"],
            self.cfg["hide_while_aiming"], self.aim_active)
        state = (visible, self.cfg["active_mode"], self.cfg["colors"][self.cfg["active_mode"]],
                 self.cfg["offset_x"], self.cfg["offset_y"], self.cfg["size"], self.cfg["thickness"])
        if not force and state == self.previous_draw:
            return
        self.previous_draw = state
        self.canvas.delete("reticle")
        if visible:
            draw_reticle(self.canvas,
                         self.sw/2 + self.cfg["offset_x"], self.sh/2 + self.cfg["offset_y"],
                         self.cfg["active_mode"], self.cfg["colors"][self.cfg["active_mode"]],
                         self.cfg["size"] / 100, self.cfg["thickness"])

    def reset(self):
        self.cfg = json.loads(json.dumps(DEFAULTS))
        self.mode_var.set(self.cfg["active_mode"])
        self.overlay_var.set(self.cfg["overlay_enabled"])
        self.only_game_var.set(self.cfg["only_in_game"])
        self.hide_ads_var.set(self.cfg["hide_while_aiming"])
        self.ads_input_var.set(self.cfg["aim_input"])
        self.aim_tracker.reset()
        self.aim_active = False
        self.x_var.set(0)
        self.y_var.set(0)
        self.size_var.set(100)
        self.thick_var.set(3)
        for number in "12345":
            self.slots[number].set(self.cfg["slot_mapping"][number])
        self.refresh_previews()
        self.render(True)
        self.save_later()

    def hide(self):
        self.window.withdraw()

    def toggle_settings(self):
        if self.window.state() == "withdrawn":
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
        else:
            self.hide()

    def quit(self):
        config_save(self.cfg)
        self.root.destroy()

    def poll(self):
        try:
            self.in_game = game_focused()
            self.aim_active = self.aim_tracker.update(
                self.in_game, bool(user32.GetAsyncKeyState(0x02) & 0x8000),
                self.cfg["aim_input"])
            for name, code in self.KEY_CODES.items():
                pressed = bool(user32.GetAsyncKeyState(code) & 0x8000)
                if pressed and not self.down[name]:
                    if name == "F6":
                        idx = (MODES.index(self.cfg["active_mode"]) + 1) % len(MODES)
                        self.set_mode(MODES[idx])
                    elif name == "F7":
                        self.overlay_var.set(not self.overlay_var.get())
                        self.options_changed()
                    elif name == "F8":
                        self.toggle_settings()
                    elif self.in_game:
                        self.set_mode(self.cfg["slot_mapping"][name])
                self.down[name] = pressed
            if not self.cfg["overlay_enabled"]:
                self.status.set("Overlay paused - F7 to enable.")
            elif self.cfg["only_in_game"] and not self.in_game:
                self.status.set("Waiting for Creative Destruction (client.exe)...")
            elif self.in_game and self.cfg["hide_while_aiming"] and self.aim_active:
                self.status.set("Scoped / aiming - crosshair hidden. Release aim to restore.")
            else:
                self.status.set(f"Active: {self.cfg['active_mode']} - F6 style / F7 overlay / F8 settings")
            self.render()
            self.root.after(30, self.poll)
        except tk.TclError:
            pass

    def check_updates(self, silent=False):
        if self.update_busy:
            return
        self.update_busy = True
        self.update_button.configure(state=tk.DISABLED)
        self.update_status.set("Checking GitHub Releases...")
        def worker():
            try:
                result = find_update(VERSION)
                self.events.put(("found" if result else "none", result, silent))
            except Exception as exc:
                self.events.put(("error", str(exc), silent))
        threading.Thread(target=worker, daemon=True).start()

    def install_update(self, release):
        self.update_busy = True
        self.update_button.configure(state=tk.DISABLED)
        self.update_status.set(f"Downloading v{release['version']} and checking SHA256...")
        def worker():
            try:
                installer = download_verified_installer(release)
                self.events.put(("downloaded", installer, False))
            except Exception as exc:
                self.events.put(("error", str(exc), False))
        threading.Thread(target=worker, daemon=True).start()

    def poll_updates(self):
        try:
            while True:
                event, payload, silent = self.events.get_nowait()
                self.update_busy = False
                self.update_button.configure(state=tk.NORMAL)
                if event == "found":
                    self.update_status.set(f"New version v{payload['version']} available.")
                    notes = (payload.get("notes") or "").strip()[:500]
                    prompt = (f"A new version is available!\n\n"
                              f"Installed: v{VERSION}\nAvailable: v{payload['version']}\n\n"
                              f"{notes}\n\nDownload and install now?")
                    if messagebox.askyesno("sg0hann - Update Available", prompt, parent=self.window):
                        if not getattr(sys, "frozen", False):
                            messagebox.showinfo("Run the EXE",
                                "Auto-install works in the packaged Windows .exe. "
                                "Use the GitHub Releases installer.", parent=self.window)
                        else:
                            self.install_update(payload)
                elif event == "none":
                    self.update_status.set(f"You're up to date (v{VERSION}).")
                    if not silent:
                        messagebox.showinfo("Up to date", "You have the latest version.",
                                            parent=self.window)
                elif event == "error":
                    self.update_status.set("Update check/download failed.")
                    if not silent:
                        messagebox.showerror("Update error", payload, parent=self.window)
                elif event == "downloaded":
                    self.update_status.set("Verified - starting installer...")
                    try:
                        launch_installer(payload)
                        self.quit()
                        return
                    except Exception as exc:
                        self.update_status.set("Could not start installer.")
                        messagebox.showerror("Update error", str(exc), parent=self.window)
        except queue.Empty:
            pass
        try:
            self.root.after(150, self.poll_updates)
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()


def main():
    if sys.platform != "win32":
        print("Windows 10/11 required.", file=sys.stderr)
        return 1
    try:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
        CrosshairApp().run()
        return 0
    except tk.TclError as exc:
        print(f"Crosshair UI failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
