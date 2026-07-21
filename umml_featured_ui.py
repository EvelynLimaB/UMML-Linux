"""Tk integration for UMML's opt-in featured mod.

Kept separate from the upstream-derived UMML GUI so the feature can be removed
or updated without mixing third-party download policy into the core loader.
"""

from __future__ import annotations

import queue
import threading
import webbrowser
from typing import Any

import tkinter as tk
from tkinter import messagebox, ttk

from umml_featured_mods import (
    DARK_MODE_LICENSE_NAME,
    DARK_MODE_LICENSE_URL,
    DARK_MODE_SOURCE_URL,
    DARK_MODE_TITLE,
    FeaturedModManager,
)


def _notice() -> str:
    return (
        f"{DARK_MODE_TITLE} is a third-party game mod.\n\n"
        "UMML will download the creator's original archive from GameBanana only "
        "after you approve. The archive is not bundled into UMML and is not modified.\n\n"
        f"License: {DARK_MODE_LICENSE_NAME}\n"
        "Attribution and the original source page remain available in the interface.\n\n"
        "Keep the game closed while installing or disabling it. Continue?"
    )


def _set_busy(self, busy: bool, status: str | None = None) -> None:
    self._featured_busy = busy
    toggle_state = "disabled" if busy or self.region != "Global" else "normal"
    self.dark_mode_toggle.configure(state=toggle_state)
    if status:
        self.dark_mode_status.set(status)
    self.root.update_idletasks()


def _set_progress(self, message: str) -> None:
    self.dark_mode_status.set(message)
    self.progress_label.configure(text=message)
    self.root.update_idletasks()


def _offer_once(self) -> None:
    if self.region != "Global" or not self.featured_mods.should_offer():
        return
    self.featured_mods.mark_offer_complete()
    accepted = messagebox.askyesno(
        "Optional dark mode",
        _notice(),
        parent=self.root,
    )
    if accepted:
        self.dark_mode_enabled.set(True)
        _toggle(self, confirmed=True)


def _prepare_worker(self) -> None:
    try:
        prepared = self.featured_mods.prepare()
    except Exception as exc:
        self._featured_results.put(("error", str(exc)))
    else:
        self._featured_results.put(("prepared", prepared))


def _poll_results(self) -> None:
    try:
        kind, payload = self._featured_results.get_nowait()
    except queue.Empty:
        if self._featured_busy:
            self.root.after(100, lambda: _poll_results(self))
        return

    if kind == "error":
        self.dark_mode_enabled.set(False)
        _set_busy(self, False, self.featured_mods.status_text())
        messagebox.showerror(
            "Could not prepare dark mode",
            str(payload),
            parent=self.root,
        )
        return

    metadata, archive, mod_root = payload
    self.dark_mode_status.set("Installing dark-mode assets…")
    try:
        result = self.featured_mods.enable(
            metadata,
            archive,
            mod_root,
            progress=lambda message: _set_progress(self, message),
        )
    except Exception as exc:
        self.dark_mode_enabled.set(False)
        _set_busy(self, False, self.featured_mods.status_text())
        messagebox.showerror(
            "Could not install dark mode",
            str(exc),
            parent=self.root,
        )
        return

    self.dark_mode_enabled.set(True)
    self.progress_label.configure(text="Ready")
    self.progress_bar["value"] = 0
    _set_busy(self, False, self.featured_mods.status_text())
    messagebox.showinfo(
        "Dark mode enabled",
        f"Installed {result.changed} asset(s).\n"
        f"Assets not present in the current metadata: {result.skipped}.",
        parent=self.root,
    )


def _toggle(self, confirmed: bool = False) -> None:
    if self._featured_busy:
        return
    if self.region != "Global":
        self.dark_mode_enabled.set(False)
        messagebox.showwarning(
            "Unsupported game region",
            f"{DARK_MODE_TITLE} is published for the Global client.",
            parent=self.root,
        )
        return

    if self.dark_mode_enabled.get():
        if not confirmed and not messagebox.askyesno(
            "Install optional dark mode",
            _notice(),
            parent=self.root,
        ):
            self.dark_mode_enabled.set(False)
            return
        self.featured_mods.mark_offer_complete()
        _set_busy(self, True, "Downloading original archive…")
        threading.Thread(target=lambda: _prepare_worker(self), daemon=True).start()
        self.root.after(100, lambda: _poll_results(self))
        return

    _set_busy(self, True, "Restoring assets replaced by dark mode…")
    try:
        result = self.featured_mods.disable(
            progress=lambda message: _set_progress(self, message)
        )
    except Exception as exc:
        self.dark_mode_enabled.set(self.featured_mods.is_enabled())
        messagebox.showerror(
            "Could not disable dark mode",
            str(exc),
            parent=self.root,
        )
    else:
        self.dark_mode_enabled.set(self.featured_mods.is_enabled())
        if result.conflicts:
            messagebox.showwarning(
                "Dark mode partially disabled",
                "UMML restored every unchanged dark-mode file, but left files that "
                "another mod changed afterward untouched.\n\n"
                f"Conflicts: {len(result.conflicts)}\n\n"
                "Resolve those files, then switch dark mode off again to retry.",
                parent=self.root,
            )
        else:
            messagebox.showinfo(
                "Dark mode disabled",
                f"Restored {result.changed} asset(s).",
                parent=self.root,
            )
    finally:
        self.progress_label.configure(text="Ready")
        self.progress_bar["value"] = 0
        _set_busy(self, False, self.featured_mods.status_text())


def _show_details(self) -> None:
    state = self.featured_mods.read_state()
    metadata = state.get("metadata") if isinstance(state.get("metadata"), dict) else {}
    author = metadata.get("author") or "See the original GameBanana source page"
    archive_hash = state.get("archive_sha256") or "Not downloaded"
    messagebox.showinfo(
        "Featured mod license",
        f"Title: {DARK_MODE_TITLE}\n"
        f"Creator/submitter: {author}\n"
        f"Source: {DARK_MODE_SOURCE_URL}\n"
        f"License: {DARK_MODE_LICENSE_NAME}\n"
        f"License URL: {DARK_MODE_LICENSE_URL}\n\n"
        "UMML does not include or repack this archive. It downloads the original "
        "file only after user opt-in.\n\n"
        f"Local state: {self.featured_mods.state_path}\n"
        f"Downloaded archive SHA-256: {archive_hash}",
        parent=self.root,
    )


def _add_widgets(self) -> None:
    self.featured_mods = FeaturedModManager(
        dat_path=self.dat_path,
        decrypt_assets=self.decrypt_assets_internal,
    )
    self.dark_mode_enabled = tk.BooleanVar(value=self.featured_mods.is_enabled())
    self.dark_mode_status = tk.StringVar(value=self.featured_mods.status_text())
    self._featured_results: queue.Queue[tuple[str, Any]] = queue.Queue()
    self._featured_busy = False

    # The original GUI places its footer in root row 2. Move it down and insert
    # a compact, always-visible featured-mod bar above it.
    for widget in self.root.grid_slaves(row=2, column=0):
        widget.grid_configure(row=3)

    frame = ttk.LabelFrame(self.root, text="Featured optional mod", padding=(12, 8))
    frame.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 10))
    frame.columnconfigure(1, weight=1)
    self.dark_mode_toggle = ttk.Checkbutton(
        frame,
        text=f"Use {DARK_MODE_TITLE}",
        variable=self.dark_mode_enabled,
        command=lambda: _toggle(self),
    )
    self.dark_mode_toggle.grid(row=0, column=0, sticky="w", padx=(0, 12))
    ttk.Label(frame, textvariable=self.dark_mode_status).grid(
        row=0, column=1, sticky="w"
    )
    ttk.Button(
        frame,
        text="Source",
        command=lambda: webbrowser.open(DARK_MODE_SOURCE_URL),
    ).grid(row=0, column=2, padx=4)
    ttk.Button(
        frame,
        text="License",
        command=lambda: webbrowser.open(DARK_MODE_LICENSE_URL),
    ).grid(row=0, column=3, padx=(4, 0))
    ttk.Label(
        frame,
        text=(
            f"Original GameBanana archive, downloaded only after opt-in; "
            f"not included in UMML. {DARK_MODE_LICENSE_NAME}."
        ),
        wraplength=780,
        justify="left",
    ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(5, 0))

    if self.region != "Global":
        self.dark_mode_toggle.configure(state="disabled")
        self.dark_mode_enabled.set(False)
        self.dark_mode_status.set("Available for the Global client only")

    menu_name = self.root.cget("menu")
    if menu_name:
        menubar = self.root.nametowidget(menu_name)
        featured_menu = tk.Menu(menubar, tearoff=0)
        featured_menu.add_command(
            label="Toggle UM:PD Dark Mode",
            command=lambda: (
                self.dark_mode_enabled.set(not self.dark_mode_enabled.get()),
                _toggle(self),
            ),
        )
        featured_menu.add_command(label="License and local state", command=lambda: _show_details(self))
        featured_menu.add_separator()
        featured_menu.add_command(
            label="Open original source",
            command=lambda: webbrowser.open(DARK_MODE_SOURCE_URL),
        )
        menubar.add_cascade(label="Featured", menu=featured_menu)


def install_featured_ui(gui_class) -> None:
    """Attach the featured-mod UI to UMML's existing GUI class once."""

    if getattr(gui_class, "_featured_mod_ui_installed", False):
        return
    gui_class._featured_mod_ui_installed = True
    original_create_widgets = gui_class.create_widgets
    original_init = gui_class.__init__

    def create_widgets(self):
        original_create_widgets(self)
        _add_widgets(self)

    def init(self, root):
        original_init(self, root)
        self.root.geometry("960x705")
        self.root.minsize(820, 620)
        self.root.after(650, lambda: _offer_once(self))

    gui_class.create_widgets = create_widgets
    gui_class.__init__ = init
    gui_class.show_featured_mod_details = _show_details
