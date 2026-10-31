"""Native asset research workspace for the sg0hann Crosshair app.

Preview and export UI graphics from a user-selected archive; optionally create
an explicitly experimental COPY, never replacing files inside the game folder.
"""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, colorchooser, messagebox, ttk
from PIL import Image, ImageTk
from native_assets import CANDIDATES, read_candidate, recolor_white, export_preview, build_experimental_copy

BG, PANEL, CARD = "#10141B", "#1A2029", "#222A35"
FG, MUTED, ACCENT = "#F1F4F6", "#9AA5B1", "#9CE379"


class NativePanel:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.archive = tk.StringVar(value="")
        self.color = tk.StringVar(value=app.cfg["colors"]["Pickaxe"])
        self.selection = tk.StringVar(value=self._choice(580))
        self.status = tk.StringVar(value="Choose a local ui1.npk to inspect asset candidates.")
        self.images = []
        self.busy = False
        self.construct()

    @staticmethod
    def _choice(index):
        return f"{index}  ·  {CANDIDATES[index][1]}"

    def caption(self, parent, text, size=10, color=FG, bold=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI",size,"bold" if bold else "normal"),
                        wraplength=430, justify="left")

    def btn(self, parent, text, action, highlight=False):
        return tk.Button(parent, text=text, command=action, bg="#27432E" if highlight else CARD,
                         fg=ACCENT if highlight else FG, activebackground="#36563D",
                         activeforeground=FG, relief="flat", bd=0, padx=13, pady=9,
                         cursor="hand2", font=("Segoe UI",10,"bold"))

    def section(self, title):
        outer = tk.Frame(self.parent, bg=PANEL, padx=16, pady=15,
                         highlightthickness=1, highlightbackground="#303A45")
        outer.pack(fill="x", pady=(0,12))
        self.caption(outer,title,12,FG,True).pack(anchor="w",pady=(0,8))
        return outer

    def construct(self):
        info = self.section("NATIVE ASSET LAB   /   EXPERIMENTAL")
        self.caption(info, "The original combat crosshair IDs have NOT been proven. "
                           "This tab lets you compare, recolor and export image assets "
                           "without changing your installation.", 10, MUTED).pack(anchor="w")
        self.caption(info, "Any patched NPK is only an experimental copy. "
                           "It may not work in the game or may fail integrity checks.",
                     9, "#F6B17B", True).pack(anchor="w",pady=(9,0))

        controls = self.section("1   SELECT ORIGINAL ARCHIVE")
        self.caption(controls, "Your extracted ui1.npk (not a .7z split volume)",
                     9,MUTED).pack(anchor="w")
        tk.Entry(controls, textvariable=self.archive, bg=CARD, fg=FG, insertbackground=FG,
                 relief="flat").pack(fill="x",ipady=9,pady=(9,6))
        self.btn(controls, "Browse ui1.npk", self.browse).pack(anchor="w")

        candidate = self.section("2   SELECT ASSET / COLOR")
        vals=[self._choice(i) for i in CANDIDATES]
        self.combo=ttk.Combobox(candidate, textvariable=self.selection,
                                values=vals, state="readonly",width=45)
        self.combo.pack(fill="x",pady=(3,10))
        row=tk.Frame(candidate,bg=PANEL)
        row.pack(fill="x")
        tk.Entry(row, textvariable=self.color, width=12, bg=CARD, fg=FG,
                 relief="flat", insertbackground=FG).pack(side="left",ipady=8)
        self.btn(row, "Choose color", self.pick_color).pack(side="left",padx=7)
        self.btn(candidate, "Preview selected asset", self.preview, True).pack(
            fill="x",pady=(10,0))
        area=tk.Frame(candidate,bg=CARD)
        area.pack(fill="x",pady=(12,0))
        self.original_label=tk.Label(area,bg=CARD,fg=MUTED,text="Original",
                                     font=("Segoe UI",9))
        self.original_label.pack(side="left",fill="both",expand=True,pady=10)
        self.recolor_label=tk.Label(area,bg=CARD,fg=MUTED,text="Recolored preview",
                                    font=("Segoe UI",9))
        self.recolor_label.pack(side="right",fill="both",expand=True,pady=10)
        self.caption(candidate,"Exported images are previews; they are not installed.",
                     9,MUTED).pack(anchor="w",pady=(7,0))
        self.btn(candidate,"Export recolored PNG",self.export_png).pack(
            anchor="w",pady=(9,0))

        test=self.section("3   OPTIONAL EXPERIMENTAL NPK COPY")
        self.caption(test,"Creates a NEW archive under a name you choose. "
                          "Original files remain untouched. This is not a verified "
                          "in-game crosshair modification.", 9,MUTED).pack(anchor="w")
        self.btn(test,"Create experimental NPK copy…",
                 self.experimental_copy).pack(fill="x",pady=(10,0))
        self.caption(self.parent,"",9,ACCENT).pack(anchor="w")
        self.caption(self.parent,"",9,ACCENT,textvariable=self.status).pack(
            anchor="w",pady=(0,14))

    def index(self):
        return int(self.selection.get().split()[0])

    def source(self):
        path=Path(self.archive.get())
        if not path.is_file() or path.suffix.lower() != ".npk":
            raise ValueError("Select an existing .npk archive.")
        return path

    def browse(self):
        chosen=filedialog.askopenfilename(parent=self.app.window,title="Select ui1.npk",
                                         filetypes=[("NPK archives","*.npk")])
        if chosen:
            self.archive.set(chosen)
            self.preview()

    def pick_color(self):
        choice=colorchooser.askcolor(color=self.color.get(),parent=self.app.window)
        if choice and choice[1]:
            self.color.set(choice[1].upper())
            if self.archive.get():
                self.preview()

    def preview(self):
        try:
            image, metadata=read_candidate(self.source(),self.index())
            colored=recolor_white(image,self.color.get())
            thumbs=[]
            for item in (image,colored):
                target=item.copy()
                target.thumbnail((142,122),Image.Resampling.LANCZOS)
                thumbs.append(ImageTk.PhotoImage(target))
            self.images=thumbs
            self.original_label.configure(image=thumbs[0],text="")
            self.recolor_label.configure(image=thumbs[1],text="")
            self.status.set(f"Resource {metadata['id']} / {metadata['dimensions']} "
                            "— visually similar only; usage not confirmed.")
        except Exception as exc:
            self.status.set(f"Preview failed: {exc}")

    def export_png(self):
        try:
            src=self.source()
            idx=self.index()
            output=filedialog.asksaveasfilename(parent=self.app.window,
                        defaultextension=".png",filetypes=[("PNG images","*.png")],
                        initialfile=f"candidate_{idx}_{self.color.get()[1:]}.png")
            if not output:
                return
            export_preview(src,idx,self.color.get(),output)
            self.status.set(f"Exported preview PNG: {output}")
        except Exception as exc:
            messagebox.showerror("Export failed",str(exc),parent=self.app.window)

    def experimental_copy(self):
        if self.busy:
            return
        try:
            src=self.source()
            index=self.index()
            color=self.color.get()
            # Validate before prompting for output location.
            recolor_white(read_candidate(src,index)[0],color)
        except Exception as exc:
            messagebox.showerror("Invalid selection",str(exc),parent=self.app.window)
            return
        consent=messagebox.askyesno(
            "Experimental archive — not verified",
            "This does NOT identify or verify the game's native combat crosshair. "
            "It produces a modified COPY of ui1.npk, not an installed patch. "
            "The game might reject the file; using modified archives online may "
            "violate the game's rules. No anti-cheat bypass is provided.\n\n"
            "Create a separate test archive anyway?",
            parent=self.app.window)
        if not consent:
            return
        output=filedialog.asksaveasfilename(
            parent=self.app.window,
            title="Save experimental NPK (NOT inside the game installation)",
            defaultextension=".npk",filetypes=[("NPK archive","*.npk")],
            initialfile=f"ui1_EXPERIMENTAL_asset_{index}.npk")
        if not output:
            return
        out=Path(output)
        if out.resolve()==src.resolve():
            messagebox.showerror("Refused","Original file cannot be overwritten.",parent=self.app.window)
            return
        self.busy=True
        self.status.set("Building and validating the experimental COPY…")
        def worker():
            try:
                report=build_experimental_copy(src,index,color,out)
                self.app.window.after(0,lambda: self.done(report,None))
            except Exception as exc:
                err=str(exc)
                self.app.window.after(0,lambda: self.done(None,err))
        threading.Thread(target=worker,daemon=True).start()

    def done(self,report,error):
        self.busy=False
        if error:
            self.status.set("Experimental copy failed.")
            messagebox.showerror("Native Lab",error,parent=self.app.window)
            return
        self.status.set("Experimental copy created and archive read-back verified.")
        messagebox.showinfo("Saved — not game-tested",
                f"Created: {report['output']}\n\n"
                "The patched resource decodes correctly, but whether this "
                "affects the combat crosshair or passes game integrity checks "
                "is UNKNOWN. Original game files were not changed.",
                parent=self.app.window)


def add_panel(app,parent):
    app.native_panel=NativePanel(app,parent)
