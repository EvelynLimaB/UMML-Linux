#!/usr/bin/env python3
"""Cross-platform UMML entry point.

The upstream 1.5.0-hotfix implementation lives in ``UMML_core.py``.  This thin
entry point keeps that mature mod-loading code intact while supplying portable
Steam/Proton discovery, a safer startup path, diagnostics, and a responsive ttk
interface.
"""

from __future__ import annotations

import importlib
import os
import sys
import traceback
import types
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, ttk

from umml_autodetect import apply as apply_autodetect

apply_autodetect()

from umml_platform import (
    find_game_path,
    format_doctor_report,
    get_steam_libraries,
    get_steam_path,
    load_settings,
    resolve_case_sensitive_path,
)

MODLOADER_VERSION = "1.5.0-hotfix"


def run_doctor() -> int:
    """Print path discovery and dependency diagnostics without opening a GUI."""

    report, ready = format_doctor_report()
    print(report)
    print("\nPython requirements:")

    checks = (
        ("Tkinter", "tkinter", lambda module: f"Tk {module.TkVersion}"),
        ("UnityPy", "UnityPy", lambda module: getattr(module, "__version__", "installed")),
        ("vdf", "vdf", lambda module: getattr(module, "__version__", "installed")),
        ("apsw-sqlite3mc", "apsw", lambda module: getattr(module, "mc_version", "installed")),
        ("PyYAML", "yaml", lambda module: getattr(module, "__version__", "installed")),
    )
    dependencies_ready = True
    for label, module_name, describe in checks:
        try:
            module = importlib.import_module(module_name)
            print(f"  [OK] {label}: {describe(module)}")
        except Exception as exc:
            dependencies_ready = False
            print(f"  [FAIL] {label}: {exc}")

    return 0 if ready and dependencies_ready else 1


if "--doctor" in sys.argv:
    raise SystemExit(run_doctor())

# The upstream source imports winreg unconditionally. Give Linux a harmless
# placeholder so the module can load; discovery functions are already patched
# by the autodetection engine above.
if os.name != "nt" and "winreg" not in sys.modules:
    winreg_stub = types.ModuleType("winreg")
    winreg_stub.HKEY_CURRENT_USER = object()
    winreg_stub.HKEY_LOCAL_MACHINE = object()
    sys.modules["winreg"] = winreg_stub

import UMML_core as core  # noqa: E402

core.resolve_case_sensitive_path = resolve_case_sensitive_path
core.get_steam_path = get_steam_path
core.get_steam_libraries = get_steam_libraries
core.find_game_path = find_game_path
core.modloader_version = MODLOADER_VERSION


class ModLoaderGUI(core.ModLoaderGUI):
    """Upstream UMML behavior with a portable startup and refreshed shell UI."""

    def load_hachimi_dict(self):
        if not self.game_dir:
            self.hachimi_dict = {}
            return
        return super().load_hachimi_dict()

    def __init__(self, root):
        self.root = root
        self.root.title(f"UMML {MODLOADER_VERSION}")
        self.root.geometry("920x620")
        self.root.minsize(780, 540)
        self._configure_theme()

        self.startup_status = tk.StringVar(value="Starting UMML…")
        self.startup_frame = ttk.Frame(self.root, padding=28)
        self.startup_frame.pack(fill="both", expand=True)
        ttk.Label(
            self.startup_frame,
            text=f"UMML {MODLOADER_VERSION}",
            font=("TkDefaultFont", 18, "bold"),
        ).pack(pady=(55, 14))
        ttk.Label(
            self.startup_frame,
            textvariable=self.startup_status,
            anchor="center",
            justify="center",
            wraplength=650,
        ).pack(fill="x", pady=10)
        self.startup_progress = ttk.Progressbar(
            self.startup_frame,
            mode="indeterminate",
            length=380,
        )
        self.startup_progress.pack(pady=12)
        self.startup_progress.start(12)
        ttk.Label(
            self.startup_frame,
            text="On the first launch, opening the game metadata can take a little while.",
            anchor="center",
            justify="center",
        ).pack(fill="x", pady=(8, 0))
        self.root.update_idletasks()
        self.root.update()

        self._set_startup_status("Searching for Umamusume and its Steam/Proton data…")
        (
            self.dat_path,
            self.backup_path,
            self.region,
            self.game_dir,
            self.meta_path_pth,
        ) = load_settings(parent=self.root, status_callback=self._set_startup_status)

        self.meta_path_load = core.load_or_decrypt_meta_simple
        self._set_startup_status(
            "Opening game metadata… Do not close UMML during first-time cache creation."
        )
        self.meta_path = self.meta_path_load(
            self.dat_path,
            self.meta_path_pth,
            self.region,
        )

        self._set_startup_status("Building the UMML interface…")
        self.mod_path = tk.StringVar()
        self.title_text = tk.StringVar()
        self.version_text = tk.StringVar()
        self.load_hachimi_dict()

        self.startup_progress.stop()
        self.startup_frame.destroy()
        self.create_widgets()
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()

    def _set_startup_status(self, message):
        print(f"[Startup] {message}")
        if hasattr(self, "startup_status"):
            self.startup_status.set(message)
            self.root.update_idletasks()
            self.root.update()

    def _configure_theme(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        background = "#f6f3f8"
        surface = "#ffffff"
        text = "#241f2b"
        muted = "#6f6877"
        accent = "#7651a8"
        accent_hover = "#654293"
        success = "#257a55"
        danger = "#a43d4d"

        self.root.configure(background=background)
        style.configure("TFrame", background=background)
        style.configure("Surface.TFrame", background=surface)
        style.configure("TLabel", background=background, foreground=text, font=("TkDefaultFont", 10))
        style.configure("Surface.TLabel", background=surface, foreground=text)
        style.configure("Muted.TLabel", background=background, foreground=muted)
        style.configure("SurfaceMuted.TLabel", background=surface, foreground=muted)
        style.configure("Title.TLabel", background=background, foreground=text, font=("TkDefaultFont", 17, "bold"))
        style.configure("Header.TLabel", background=background, foreground=text, font=("TkDefaultFont", 20, "bold"))
        style.configure("Choice.TLabel", background=background, foreground=text, font=("TkDefaultFont", 10, "bold"))
        style.configure("Detected.TLabel", background=background, foreground=success, font=("TkDefaultFont", 9, "bold"))
        style.configure("Error.TLabel", background=background, foreground=danger)
        style.configure("Badge.TLabel", background=accent, foreground="white", padding=(8, 3), font=("TkDefaultFont", 9, "bold"))
        style.configure("TLabelframe", background=surface, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=surface, foreground=text, font=("TkDefaultFont", 10, "bold"))
        style.configure("TButton", padding=(10, 7))
        style.configure("Accent.TButton", background=accent, foreground="white", padding=(12, 8), font=("TkDefaultFont", 10, "bold"))
        style.map("Accent.TButton", background=[("active", accent_hover), ("disabled", "#b8adbf")])
        style.configure("Danger.TButton", foreground=danger)
        style.configure("Horizontal.TProgressbar", troughcolor="#e8e1ec", background=accent)

    def create_widgets(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        character_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Character", menu=character_menu)
        asset_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Assets", menu=asset_menu)
        single_mode_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Single Mode", menu=single_mode_menu)
        story_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Story", menu=story_menu)
        modelreplace_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Model Replace", menu=modelreplace_menu)
        experimental_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Experimental", menu=experimental_menu)

        asset_menu.add_command(label="Clean unused assets", command=self.clean_unused_assets)
        character_menu.add_command(label="Attributes", command=self.open_chara_settings)
        character_menu.add_command(label="Personality", command=self.open_personality_settings)
        character_menu.add_command(label="Dress", command=self.open_dress_settings)
        single_mode_menu.add_command(label="Training", command=self.open_training_settings)
        story_menu.add_command(label="Concert", command=self.open_story_concert)
        modelreplace_menu.add_command(label="Swap Character", command=self.open_swap_character)
        experimental_menu.add_command(
            label="Merge Global translation into Japanese",
            command=self.force_translate_english,
        )

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Detected paths", command=self.show_detected_paths)
        help_menu.add_command(label="Run diagnostics", command=self.show_doctor_report)
        help_menu.add_separator()
        help_menu.add_command(label="About UMML", command=self.show_about)

        header = ttk.Frame(self.root, padding=(22, 16, 22, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="UMML", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Load, preview, back up, and restore Umamusume mods.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        badges = ttk.Frame(header)
        badges.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Label(badges, text=self.region, style="Badge.TLabel").pack(side="left", padx=4)
        ttk.Label(badges, text=MODLOADER_VERSION, style="Badge.TLabel").pack(side="left", padx=4)

        content = ttk.Frame(self.root, padding=(22, 4, 22, 12))
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(1, weight=1)

        mod_frame = ttk.LabelFrame(content, text="Mod folder", padding=12)
        mod_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        mod_frame.columnconfigure(0, weight=1)
        ttk.Entry(mod_frame, textvariable=self.mod_path).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(mod_frame, text="Browse…", command=self.browse_folder).grid(row=0, column=1, padx=4)
        ttk.Button(mod_frame, text="Reload", command=self.reload).grid(row=0, column=2, padx=4)
        ttk.Button(mod_frame, text="Preview", command=self.preview_assets).grid(row=0, column=3, padx=(4, 0))

        info_frame = ttk.LabelFrame(content, text="Mod information", padding=12)
        info_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(3, weight=1)
        ttk.Label(info_frame, textvariable=self.title_text, style="Surface.TLabel", font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(info_frame, textvariable=self.version_text, style="SurfaceMuted.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 8))
        ttk.Label(info_frame, text="Description", style="SurfaceMuted.TLabel").grid(row=2, column=0, sticky="w")
        self.description_box = tk.Text(
            info_frame,
            height=10,
            wrap="word",
            state="disabled",
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=8,
            background="#faf8fb",
            foreground="#241f2b",
        )
        self.description_box.grid(row=3, column=0, sticky="nsew", pady=(4, 0))

        control_frame = ttk.LabelFrame(content, text="Actions", padding=12)
        control_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        control_frame.columnconfigure(0, weight=1)
        self.assets_load_btn = ttk.Button(
            control_frame,
            text="Load mod assets",
            state="disabled",
            command=self.load_assets,
            style="Accent.TButton",
        )
        self.assets_load_btn.grid(row=0, column=0, sticky="ew", pady=(0, 7))
        self.assets_load_raw_btn = ttk.Button(control_frame, text="Load assets manually", command=self.load_assets_manual)
        self.assets_load_raw_btn.grid(row=1, column=0, sticky="ew", pady=7)
        self.restore_btn = ttk.Button(control_frame, text="Restore original assets", command=self.restore_original_assets)
        self.restore_btn.grid(row=2, column=0, sticky="ew", pady=7)
        ttk.Separator(control_frame).grid(row=3, column=0, sticky="ew", pady=10)
        self.delete_db_btn = ttk.Button(
            control_frame,
            text="Delete master database",
            command=self.delete_master_db,
            style="Danger.TButton",
        )
        self.delete_db_btn.grid(row=4, column=0, sticky="ew", pady=7)
        ttk.Label(
            control_frame,
            text="Keep the game closed while loading or restoring assets.",
            style="SurfaceMuted.TLabel",
            wraplength=260,
            justify="left",
        ).grid(row=5, column=0, sticky="sw", pady=(14, 0))
        control_frame.rowconfigure(5, weight=1)

        progress_frame = ttk.LabelFrame(content, text="Progress", padding=12)
        progress_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        progress_frame.columnconfigure(0, weight=1)
        self.progress_label = ttk.Label(progress_frame, text="Ready", style="Surface.TLabel")
        self.progress_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=1, column=0, sticky="ew")

        footer = ttk.Frame(self.root, padding=(22, 0, 22, 14))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, text=f"Game data: {self.dat_path}", style="Muted.TLabel").grid(row=0, column=0, sticky="w")

    def show_detected_paths(self):
        lines = [
            f"Region: {self.region}",
            f"Game directory: {self.game_dir}",
            f"Data directory: {self.dat_path}",
            f"Metadata: {self.meta_path_pth}",
            f"Backup directory: {self.backup_path}",
        ]
        messagebox.showinfo("UMML detected paths", "\n\n".join(lines), parent=self.root)

    def show_doctor_report(self):
        report, _ready = format_doctor_report()
        window = tk.Toplevel(self.root)
        window.title("UMML diagnostics")
        window.geometry("780x520")
        window.minsize(620, 420)
        frame = ttk.Frame(window, padding=12)
        frame.pack(fill="both", expand=True)
        text_box = tk.Text(frame, wrap="none", font=("TkFixedFont", 10))
        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=text_box.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=text_box.xview)
        text_box.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        text_box.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text_box.insert("1.0", report)
        text_box.configure(state="disabled")

    def show_about(self):
        messagebox.showinfo(
            "About UMML",
            f"UMML {MODLOADER_VERSION}\n\n"
            "Cross-platform Umamusume mod loader with Windows, Linux, Steam, "
            "Proton, DMM, and Komoe path support.\n\n"
            "See README.md for credits, safety notes, and contribution details.",
            parent=self.root,
        )

    def delete_master_db(self):
        db_path = os.path.join(os.path.dirname(self.dat_path), "master", "master.mdb")
        if not os.path.isfile(db_path):
            messagebox.showinfo("Info", "master.mdb not found, nothing to delete.", parent=self.root)
            return
        if not messagebox.askyesno(
            "Confirm Delete",
            "This will delete master.mdb.\n\nThe game will download a fresh copy after login.\n\nContinue?",
            parent=self.root,
        ):
            return
        try:
            os.remove(db_path)
            messagebox.showinfo(
                "Deleted",
                "master.mdb deleted successfully.\nRe-login to download a new database.",
                parent=self.root,
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Could not delete database:\n{exc}", parent=self.root)


def _show_fatal_gui_error(root, title, exc):
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(details, file=sys.stderr)
    try:
        messagebox.showerror(
            title,
            f"{exc}\n\nFull details were written to the UMML log.",
            parent=root,
        )
    except Exception:
        pass


def _tk_callback_exception(root, exc_type, exc_value, exc_traceback):
    details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(details, file=sys.stderr)
    try:
        messagebox.showerror(
            "UMML Error",
            f"{exc_value}\n\nFull details were written to the UMML log.",
            parent=root,
        )
    except Exception:
        pass


def main() -> int:
    root = tk.Tk()
    root.report_callback_exception = (
        lambda exc_type, exc_value, exc_tb: _tk_callback_exception(
            root, exc_type, exc_value, exc_tb
        )
    )
    try:
        ModLoaderGUI(root)
    except SystemExit:
        try:
            root.destroy()
        finally:
            raise
    except Exception as exc:
        _show_fatal_gui_error(root, "UMML Startup Error", exc)
        root.destroy()
        return 1
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
