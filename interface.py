"""Wide, low-clutter settings UI for sg0hann Crosshair Color Lab.

Pure tkinter, so the Windows executable needs no external UI runtime.
Keeps overlay mechanics in the main application.
"""
import tkinter as tk
from tkinter import ttk

BG = "#10141B"
SIDEBAR = "#0C1016"
PANEL = "#1A2029"
CARD = "#222A35"
CARD_HOVER = "#2B3643"
BORDER = "#2B343E"
TEXT = "#F1F4F6"
MUTED = "#9AA5B1"
ACCENT = "#9CE379"
GREEN_DARK = "#253F2D"
CANVAS_BG = "#141A23"
FONT = "Segoe UI"


def label(parent, text="", size=10, color=TEXT, bold=False, **kw):
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                    font=(FONT, size, "bold" if bold else "normal"), **kw)


def action(parent, caption, command, primary=False, width=None):
    base = GREEN_DARK if primary else CARD
    active = "#34583A" if primary else CARD_HOVER
    btn = tk.Button(parent, text=caption, command=command, bg=base,
                    fg=ACCENT if primary else TEXT, activebackground=active,
                    activeforeground=TEXT, font=(FONT, 10, "bold"),
                    relief="flat", bd=0, cursor="hand2", padx=15, pady=10,
                    highlightthickness=0, width=width)
    btn.bind("<Enter>", lambda e: btn.configure(bg=active))
    btn.bind("<Leave>", lambda e: btn.configure(bg=base))
    return btn


def card(parent, padx=17, pady=14):
    shell = tk.Frame(parent, bg=PANEL, padx=padx, pady=pady,
                     highlightbackground=BORDER, highlightthickness=1)
    return shell


def header(parent, kicker, title, subtitle=None):
    label(parent, kicker, 9, ACCENT, True).pack(anchor="w")
    label(parent, title, 16, TEXT, True).pack(anchor="w", pady=(3, 0))
    if subtitle:
        label(parent, subtitle, 9, MUTED, wraplength=490,
              justify="left").pack(anchor="w", pady=(3, 0))


def build_interface(app):
    w = app.window
    w.configure(bg=BG)
    width = max(850, min(1180, app.sw - 60))
    height = max(650, min(772, app.sh - 85))
    w.geometry(f"{width}x{height}+{max(0, (app.sw-width)//2)}+{max(0, (app.sh-height)//2)}")
    w.resizable(False, False)

    style = ttk.Style(w)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Crosshair.TCombobox", fieldbackground=CARD, background=CARD,
                    foreground=TEXT, arrowcolor=ACCENT, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=6)
    style.map("Crosshair.TCombobox", fieldbackground=[("readonly", CARD)],
              foreground=[("readonly", TEXT)])

    app.nav_buttons = {}
    app.pages = {}
    app.page_shells = {}
    app.page_canvases = {}
    app.mode_tiles = {}
    app.color_buttons = {}
    app.previews = {}
    app.scale_labels = {}
    app.reactive_labels = []

    shell = tk.Frame(w, bg=BG)
    shell.pack(fill="both", expand=True)

    sidebar = tk.Frame(shell, bg=SIDEBAR, width=215)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    brand = tk.Frame(sidebar, bg=SIDEBAR, padx=23, pady=24)
    brand.pack(fill="x")
    label(brand, "sg0hann", 20, TEXT, True).pack(anchor="w")
    label(brand, "CROSSHAIR  /  COLOR LAB", 9, ACCENT, True).pack(anchor="w", pady=(3, 0))
    tk.Frame(sidebar, height=1, bg=BORDER).pack(fill="x", padx=22, pady=(2, 17))
    label(sidebar, "WORKSPACE", 9, MUTED, True).pack(anchor="w", padx=24, pady=(0, 10))

    def page_button(key, caption, symbol):
        btn = tk.Button(sidebar, text=f"{symbol}    {caption}", anchor="w",
                        bg=SIDEBAR, fg=MUTED, font=(FONT, 11, "bold"),
                        activebackground=CARD, activeforeground=TEXT,
                        relief="flat", bd=0, padx=22, pady=14, cursor="hand2",
                        command=lambda k=key: show_page(app, k))
        btn.pack(fill="x", padx=10, pady=2)
        btn.bind("<Enter>", lambda e, k=key, b=btn:
                 b.configure(bg=CARD if app.current_page != k else GREEN_DARK))
        btn.bind("<Leave>", lambda e, k=key, b=btn:
                 b.configure(bg=GREEN_DARK if app.current_page == k else SIDEBAR))
        app.nav_buttons[key] = btn

    page_button("Crosshair", "Crosshair", "◎")
    page_button("Gameplay", "Gameplay", "⌘")
    page_button("Native Lab", "Native Lab", "◉")
    page_button("Updates", "Updates", "↻")

    left_footer = tk.Frame(sidebar, bg=SIDEBAR)
    left_footer.pack(side="bottom", fill="x", padx=23, pady=21)
    tk.Frame(left_footer, height=1, bg=BORDER).pack(fill="x", pady=(0, 17))
    label(left_footer, f"VERSION  v{app.version}", 9, MUTED, True).pack(anchor="w")
    label(left_footer, "Built for Creative Destruction", 9, MUTED).pack(anchor="w", pady=(5, 0))
    action(left_footer, "Quit app", app.quit).pack(fill="x", pady=(15, 0))

    workspace = tk.Frame(shell, bg=BG)
    workspace.pack(side="left", fill="both", expand=True)

    top = tk.Frame(workspace, bg=BG, padx=25, pady=17)
    top.pack(fill="x")
    top_left = tk.Frame(top, bg=BG)
    top_left.pack(side="left")
    app.page_title = tk.StringVar(value="Crosshair")
    app.page_subtitle = tk.StringVar(value="Adjust the look and feel of every weapon.")
    label(top_left, "", 20, TEXT, True, textvariable=app.page_title).pack(anchor="w")
    label(top_left, "", 10, MUTED, textvariable=app.page_subtitle).pack(anchor="w", pady=(3, 0))
    right = tk.Frame(top, bg=BG)
    right.pack(side="right", pady=(3, 0))
    action(right, "Hide to game  →", app.hide, primary=True).pack(side="right")
    status_area = tk.Frame(right, bg=BG)
    status_area.pack(side="right", padx=(0, 15))
    app.game_badge = tk.Label(status_area, textvariable=app.game_status, bg="#2E2427",
                              fg="#FF9C9C", font=(FONT, 10, "bold"), padx=12, pady=6)
    app.game_badge.pack(anchor="e")
    label(status_area, "", 8, MUTED, textvariable=app.game_detail).pack(anchor="e", pady=(4,0))

    tk.Frame(workspace, height=1, bg=BORDER).pack(fill="x", padx=25)

    footer = tk.Frame(workspace, bg=BG, padx=25, pady=11)
    footer.pack(side="bottom", fill="x")
    tk.Frame(footer, height=1, bg=BORDER).pack(fill="x", pady=(0, 9))
    label(footer, "", 9, MUTED, textvariable=app.status,
          wraplength=650, anchor="w").pack(side="left", fill="x", expand=True)
    action(footer, "Reset defaults", app.reset).pack(side="right")

    main = tk.Frame(workspace, bg=BG, padx=25, pady=21)
    main.pack(fill="both", expand=True)
    preview = tk.Frame(main, bg=PANEL, width=295,
                       highlightthickness=1, highlightbackground=BORDER)
    preview.pack(side="right", fill="y", padx=(16, 0))
    preview.pack_propagate(False)
    preview_top = tk.Frame(preview, bg=PANEL, padx=19, pady=19)
    preview_top.pack(fill="x")
    label(preview_top, "LIVE PREVIEW", 9, ACCENT, True).pack(anchor="w")
    label(preview_top, "Your active reticle", 14, TEXT, True).pack(anchor="w", pady=(5, 0))
    app.preview_canvas = tk.Canvas(preview, height=270, bg=CANVAS_BG,
                                   bd=0, highlightthickness=0)
    app.preview_canvas.pack(fill="x", padx=15, pady=(5, 15))
    preview_meta = tk.Frame(preview, bg=PANEL, padx=19)
    preview_meta.pack(fill="x")
    app.preview_name = tk.StringVar(value="")
    app.preview_color = tk.StringVar(value="")
    label(preview_meta, "", 13, TEXT, True, textvariable=app.preview_name).pack(anchor="w")
    label(preview_meta, "", 10, MUTED, textvariable=app.preview_color).pack(anchor="w", pady=(6, 0))
    label(preview_meta, "Preview is illustrative. Your original game HUD remains underneath.",
          9, MUTED, wraplength=238, justify="left").pack(anchor="w", pady=(17, 0))

    content = tk.Frame(main, bg=BG)
    content.pack(side="left", fill="both", expand=True)
    for key in ("Crosshair", "Gameplay", "Native Lab", "Updates"):
        shell = tk.Frame(content, bg=BG)
        shell.place(relx=0, rely=0, relwidth=1, relheight=1)
        surface = tk.Canvas(shell, bg=BG, bd=0, highlightthickness=0)
        surface.pack(side="left", fill="both", expand=True)
        scroll = tk.Scrollbar(shell, orient="vertical", command=surface.yview,
                              bg=CARD, activebackground=CARD_HOVER,
                              troughcolor=BG, relief="flat", width=9)
        scroll.pack(side="right", fill="y")
        surface.configure(yscrollcommand=scroll.set)
        frame = tk.Frame(surface, bg=BG)
        window_id = surface.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda _e, cv=surface:
                   cv.configure(scrollregion=cv.bbox("all")))
        surface.bind("<Configure>", lambda e, cv=surface, wid=window_id:
                     cv.itemconfigure(wid, width=e.width))
        app.pages[key] = frame
        app.page_shells[key] = shell
        app.page_canvases[key] = surface

    def wheel(event):
        cv = app.page_canvases.get(app.current_page)
        if cv is not None and app.window.winfo_containing(event.x_root, event.y_root):
            cv.yview_scroll(-1 if event.delta > 0 else 1, "units")
    app.window.bind("<MouseWheel>", wheel, add="+")
    app.window.bind_all("<MouseWheel>", wheel, add="+")

    create_crosshair_page(app, app.pages["Crosshair"])
    create_gameplay_page(app, app.pages["Gameplay"])
    from native_panel import add_panel
    add_panel(app, app.pages["Native Lab"])
    create_updates_page(app, app.pages["Updates"])
    app.current_page = ""
    show_page(app, "Crosshair")
    app.preview_canvas.bind("<Configure>", lambda _: refresh_interface(app))


def create_crosshair_page(app, parent):
    modes = card(parent)
    modes.pack(fill="x", pady=(0, 13))
    header(modes, "01  /  RETICLE", "Crosshair styles", "Choose a weapon style and set its own color.")
    list_area = tk.Frame(modes, bg=PANEL)
    list_area.pack(fill="x", pady=(12, 0))
    for mode in ("Shotgun", "AR / Sniper", "Sniper", "Pickaxe"):
        tile = tk.Frame(list_area, bg=CARD, height=62, padx=12,
                        highlightthickness=1, highlightbackground=BORDER)
        tile.pack(fill="x", pady=3)
        tile.pack_propagate(False)
        ico = tk.Canvas(tile, width=52, height=50, bg=CARD, bd=0, highlightthickness=0)
        ico.pack(side="left")
        app.previews[mode] = ico
        info = tk.Frame(tile, bg=CARD)
        info.pack(side="left", padx=(9, 0), fill="both", expand=True)
        label(info, mode, 11, TEXT, True).pack(anchor="w", pady=(13, 0))
        hex_label = label(info, app.cfg["colors"][mode], 9, MUTED)
        hex_label.pack(anchor="w")
        btn = action(tile, "Color", lambda m=mode: app.pick_color(m))
        btn.pack(side="right", padx=(8, 0))
        selector = tk.Button(tile, text="Use", command=lambda m=mode: choose_mode(app, m),
                             bg=CARD, fg=ACCENT, activebackground=CARD_HOVER,
                             activeforeground=ACCENT, relief="flat", bd=0,
                             font=(FONT, 10, "bold"), cursor="hand2", padx=9, pady=8)
        selector.pack(side="right")
        app.mode_tiles[mode] = (tile, selector, hex_label)
        app.color_buttons[mode] = btn

    align = card(parent)
    align.pack(fill="x")
    header(align, "02  /  FEEL", "Size & alignment", "Updates instantly. Fine-tune the overlay's placement.")
    for title, var, lo, hi, key in (
        ("Size", app.size_var, 50, 200, "size"),
        ("Thickness", app.thick_var, 2, 8, "thickness"),
        ("Horizontal", app.x_var, -500, 500, "offset_x"),
        ("Vertical", app.y_var, -500, 500, "offset_y"),
    ):
        row = tk.Frame(align, bg=PANEL)
        row.pack(fill="x", pady=(8, 0))
        bar = tk.Frame(row, bg=PANEL)
        bar.pack(fill="x")
        label(bar, title, 10, TEXT, True).pack(side="left")
        numeric = tk.StringVar(value=str(var.get()))
        label(bar, "", 9, ACCENT, True, textvariable=numeric).pack(side="right")
        app.scale_labels[key] = numeric
        slider = tk.Scale(row, from_=lo, to=hi, orient="horizontal",
                          resolution=1, variable=var, showvalue=False,
                          bg=PANEL, fg=TEXT, troughcolor=CARD,
                          activebackground=ACCENT, highlightthickness=0,
                          bd=0, sliderrelief="flat", sliderlength=15,
                          width=8, command=lambda _val: on_scale(app))
        slider.pack(fill="x")


def create_gameplay_page(app, parent):
    behavior = card(parent)
    behavior.pack(fill="x", pady=(0, 14))
    header(behavior, "01  /  BEHAVIOR", "In-game behavior",
           "Keep the overlay in sync with your gameplay.")
    toggles = (
        ("Enable overlay", app.overlay_var, "Show the colored crosshair."),
        ("Show only in Creative Destruction", app.only_game_var,
         "Hide automatically when another window is focused."),
        ("Hide when sniper scoped", app.hide_ads_var,
         "Sniper scopes hide the overlay; AR and shotgun ADS shrink."),
        ("Build-mode circular reticle", app.build_reticle_var,
         "Show pickaxe-style circle when switching to builds."),
    )
    for title, var, desc in toggles:
        row = tk.Frame(behavior, bg=PANEL)
        row.pack(fill="x", pady=(12, 1))
        switch = tk.Checkbutton(row, text=title, variable=var,
                                command=app.options_changed, bg=PANEL,
                                fg=TEXT, activebackground=PANEL,
                                activeforeground=TEXT, selectcolor=CARD,
                                font=(FONT, 10, "bold"), bd=0)
        switch.pack(anchor="w")
        label(row, desc, 9, MUTED).pack(anchor="w", padx=25)

    reactive = card(parent)
    reactive.pack(fill="x", pady=(0, 14))
    header(reactive, "02  /  REACTIVE SPREAD", "Spray & jump tracking",
           "Fast input-based approximation: LMB expands the gun reticle, "
           "Space adds jump spread. No game memory or screen capture.")
    tk.Checkbutton(
        reactive, text="Enable reactive crosshair spread",
        variable=app.reactive_var, command=app.options_changed,
        bg=PANEL, fg=TEXT, selectcolor=CARD,
        activebackground=PANEL, activeforeground=TEXT,
        font=(FONT, 10, "bold"), relief="flat", bd=0
    ).pack(anchor="w", pady=(12, 5))
    for title, var, lower, upper, suffix in (
        ("AR spray expansion", app.spray_var, 0, 180, "%"),
        ("AR jump expansion", app.jump_var, 0, 140, "%"),
        ("Shotgun firing expansion", app.shotgun_spray_var, 0, 100, "%"),
        ("Shotgun jump expansion", app.shotgun_jump_var, 0, 100, "%"),
        ("Recovery time", app.recovery_var, 100, 1500, " ms"),
    ):
        row = tk.Frame(reactive, bg=PANEL)
        row.pack(fill="x", pady=(7, 1))
        top = tk.Frame(row, bg=PANEL)
        top.pack(fill="x")
        label(top, title, 10, TEXT, True).pack(side="left")
        value = tk.StringVar(value=f"{var.get()}{suffix}")
        label(top, "", 9, ACCENT, True, textvariable=value).pack(side="right")
        app.reactive_labels.append((var, value, suffix))
        tk.Scale(
            row, from_=lower, to=upper, orient="horizontal",
            variable=var, resolution=10 if suffix == " ms" else 5,
            showvalue=False, bg=PANEL, fg=TEXT, troughcolor=CARD,
            activebackground=ACCENT, highlightthickness=0,
            bd=0, sliderrelief="flat", sliderlength=15,
            width=8, command=lambda _v: on_scale(app)
        ).pack(fill="x")
    action(reactive, "Preview spray + jump →",
           lambda: test_spread_preview(app), primary=True).pack(anchor="w", pady=(12, 3))
    label(reactive, "Input-based bloom is still approximate; the white HUD may expand "
          "differently. Building/pickaxe reticles never expand.", 9, MUTED,
          wraplength=430, justify="left").pack(anchor="w", pady=(8, 0))

    vision = card(parent)
    vision.pack(fill="x", pady=(0, 14))
    header(vision, "03  /  VISION ASSIST  ·  EXPERIMENTAL",
           "Track the original reticle",
           "Reads a small screen-center crop, searches for symmetric white HUD "
           "lines or rings, and blends measurements only when confidence is high.")
    tk.Checkbutton(
        vision, text="Enable experimental vision assistance",
        variable=app.vision_var, command=app.options_changed,
        bg=PANEL, fg=TEXT, selectcolor=CARD,
        activebackground=PANEL, activeforeground=TEXT,
        font=(FONT, 10, "bold"), relief="flat", bd=0
    ).pack(anchor="w", pady=(12, 5))
    label(vision, "", 9, ACCENT,
          textvariable=app.vision_state, wraplength=420).pack(anchor="w")
    label(vision, "Calibrate automatically: hold a gun unzoomed and stand still "
          "with the original white crosshair visible for a moment. Use a colored "
          "overlay (not pure white). Scenes with bright textures may fool detection. "
          "No measured 97% accuracy claim.", 9, MUTED, wraplength=435,
          justify="left").pack(anchor="w", pady=(7, 0))
    action(vision, "Reset visual baseline",
           app.reset_vision_baseline).pack(anchor="w", pady=(10,0))

    ads_tuning = card(parent)
    ads_tuning.pack(fill="x", pady=(0, 14))
    header(ads_tuning, "04  /  AIMING", "ARS + Shotgun ADS shrink",
           "Right mouse zoom reduces spread; sniper scope stays hidden.")
    for title, var in (
        ("AR ADS reticle size", app.ar_ads_var),
        ("Shotgun ADS reticle size", app.shotgun_ads_var),
    ):
        row = tk.Frame(ads_tuning, bg=PANEL)
        row.pack(fill="x", pady=(8,1))
        text_row = tk.Frame(row,bg=PANEL)
        text_row.pack(fill="x")
        label(text_row,title,10,TEXT,True).pack(side="left")
        value=tk.StringVar(value=f"{var.get()}%")
        app.reactive_labels.append((var,value,"%"))
        label(text_row,"",9,ACCENT,True,textvariable=value).pack(side="right")
        tk.Scale(row,from_=40,to=100,orient="horizontal",resolution=1,
                 variable=var,showvalue=False,bg=PANEL,fg=TEXT,troughcolor=CARD,
                 activebackground=ACCENT,highlightthickness=0,bd=0,
                 sliderrelief="flat",width=8,command=lambda _v: on_scale(app)).pack(fill="x")


    ads = card(parent)
    ads.pack(fill="x", pady=(0, 14))
    header(ads, "05  /  INPUT", "Right-click behavior",
           "Choose the same aiming mode you use in-game.")
    selection = tk.Frame(ads, bg=PANEL)
    selection.pack(fill="x", pady=(12, 0))
    app.aim_buttons = {}
    for option in ("Hold", "Toggle"):
        b = action(selection, option, lambda m=option: choose_aim(app, m))
        b.pack(side="left", padx=(0, 8))
        app.aim_buttons[option] = b

    mapping = card(parent)
    mapping.pack(fill="x")
    header(mapping, "06  /  BINDS", "Weapon slot mapping",
           "Your 1–5 keys select the corresponding reticle.")
    grid = tk.Frame(mapping, bg=PANEL)
    grid.pack(fill="x", pady=(12, 0))
    for key in "12345":
        cell = tk.Frame(grid, bg=PANEL)
        cell.pack(fill="x", pady=3)
        label(cell, f"Slot  {key}", 10, TEXT, True).pack(side="left")
        cb = ttk.Combobox(cell, values=("Shotgun", "AR / Sniper", "Sniper", "Pickaxe"),
                          textvariable=app.slots[key], state="readonly", width=17,
                          style="Crosshair.TCombobox")
        cb.pack(side="right")
        cb.bind("<<ComboboxSelected>>", lambda _e: app.options_changed())


def create_updates_page(app, parent):
    updates = card(parent, padx=20, pady=20)
    updates.pack(fill="x", pady=(0, 14))
    header(updates, "RELEASE CHANNEL  /  GITHUB", "Stay up to date",
           "Automatic startup checks, with your approval before installing.")
    label(updates, f"Installed: v{app.version}", 15, TEXT, True).pack(anchor="w", pady=(23, 8))
    label(updates, "", 10, MUTED, textvariable=app.update_status,
          wraplength=445, justify="left").pack(anchor="w", pady=(0, 16))
    app.update_button = action(updates, "Check for updates  ↗",
                               lambda: app.check_updates(silent=False), primary=True)
    app.update_button.pack(anchor="w")
    notes = card(parent)
    notes.pack(fill="x")
    header(notes, "ABOUT", "Designed for gameplay", "No injection, no game-file changes.")
    for item in (
        "✓  Installer downloads only after confirmation.",
        "✓  Updates are verified with SHA-256 checksums.",
        "✓  Your colors, offsets and key mappings are saved.",
        "✓  Borderless-windowed gameplay is recommended.",
    ):
        label(notes, item, 10, MUTED).pack(anchor="w", pady=(12, 0))


def choose_mode(app, mode):
    app.set_mode(mode)
    refresh_interface(app)


def choose_aim(app, mode):
    app.ads_input_var.set(mode)
    app.options_changed()
    refresh_interface(app)


def test_spread_preview(app):
    shotgun=app.cfg["active_mode"]=="Shotgun"
    fire=app.cfg["shotgun_spray_percent"] if shotgun else app.cfg["spray_percent"]
    jump=app.cfg["shotgun_jump_percent"] if shotgun else app.cfg["jump_percent"]
    app.preview_test_multiplier = 1.0 + (fire + jump)/100.0
    refresh_interface(app)
    if getattr(app, "spread_preview_job", None):
        app.window.after_cancel(app.spread_preview_job)
    app.spread_preview_job = app.window.after(850, lambda: reset_spread_preview(app))


def reset_spread_preview(app):
    app.preview_test_multiplier = 1.0
    app.spread_preview_job = None
    refresh_interface(app)


def on_scale(app):
    if not getattr(app, "scale_labels", None):
        return
    app.options_changed()
    refresh_interface(app)


def show_page(app, key):
    app.current_page = key
    titles = {
        "Crosshair": ("Crosshair", "Customize every weapon with precision."),
        "Gameplay": ("Gameplay", "Automatic switching and scope behavior."),
        "Native Lab": ("Native Lab", "Experimental NPK candidate research and safe exports."),
        "Updates": ("Updates", "Version management and safety."),
    }
    app.page_title.set(titles[key][0])
    app.page_subtitle.set(titles[key][1])
    app.page_shells[key].tkraise()
    for name, btn in app.nav_buttons.items():
        selected = name == key
        btn.configure(bg=GREEN_DARK if selected else SIDEBAR,
                      fg=ACCENT if selected else MUTED)
    refresh_interface(app)


def refresh_interface(app):
    draw_reticle = app.draw_reticle
    if not hasattr(app, "preview_canvas"):
        return
    for mode, canvas in app.previews.items():
        canvas.delete("all")
        color = app.cfg["colors"][mode]
        canvas.configure(bg=CARD)
        draw_reticle(canvas, 26, 25, mode, color, .42, 2, tag="preview")
        if mode in app.mode_tiles:
            tile, select, hex_label = app.mode_tiles[mode]
            chosen = app.cfg["active_mode"] == mode
            tile.configure(highlightbackground=ACCENT if chosen else BORDER)
            select.configure(text="Selected" if chosen else "Use",
                             fg=ACCENT if chosen else MUTED)
            hex_label.configure(text=color)
    for key, var in app.scale_labels.items():
        var.set(str(app.cfg.get(key, "")))
    if hasattr(app, "aim_buttons"):
        for mode, btn in app.aim_buttons.items():
            active = app.cfg["aim_input"] == mode
            btn.configure(fg=ACCENT if active else TEXT,
                          bg=GREEN_DARK if active else CARD)
    for var, label_var, suffix in getattr(app, "reactive_labels", []):
        label_var.set(f"{var.get()}{suffix}")
    mode = app.cfg["active_mode"]
    color = app.cfg["colors"][mode]
    app.preview_name.set(mode)
    app.preview_color.set(
        f"Color {color}   /   Size {app.cfg['size']}%   /   "
        f"Bloom ×{getattr(app, 'preview_test_multiplier', 1.0):.2f}"
    )
    canvas = app.preview_canvas
    canvas.delete("all")
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    if width < 50:
        width = 263
    if height < 50:
        height = 270
    cx, cy = width / 2, height / 2
    for i in range(30, width, 30):
        canvas.create_line(i, 0, i, height, fill="#1F2935")
    for i in range(30, height, 30):
        canvas.create_line(0, i, width, i, fill="#1F2935")
    canvas.create_oval(cx-94, cy-94, cx+94, cy+94, outline="#2E3945")
    canvas.create_line(cx, 0, cx, height, fill="#273541", dash=(4, 5))
    canvas.create_line(0, cy, width, cy, fill="#273541", dash=(4, 5))
    scale = 1.17 * app.cfg["size"] / 100
    draw_reticle(canvas, cx, cy, mode, color, scale, app.cfg["thickness"],
                 tag="preview", spread=getattr(app, "preview_test_multiplier", 1.0))
