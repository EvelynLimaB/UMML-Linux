from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable

from .installations import ManagerInstallation, detect_preferred_installation
from .process import running_game_processes
from .studio import LegacyToolLauncher, open_path
from .ui_theme import SURFACE, TEXT


class SystemActions:
    def launch_legacy_tool(self, tool_id: str):
        try:
            LegacyToolLauncher().launch(
                tool_id,
                dat_path=self.dat_path.get(),
                game_dir=self.game_dir.get(),
                meta_path=self.meta_path.get(),
                region=self.region.get(),
            )
            self.status.set("Opened UMML Studio compatibility host")
        except Exception as exc:
            messagebox.showerror(
                "Could not open legacy tool", str(exc), parent=self.root
            )

    def autofill_installation(self, automatic: bool = False):
        """Detect Steam/Proton paths and prepare the readable metadata cache."""

        def completed(installation: ManagerInstallation):
            self.dat_path.set(str(installation.dat_path))
            self.meta_path.set(str(installation.meta_path))
            self.game_dir.set(str(installation.game_dir))
            self.region.set(installation.region)
            if installation.region in {"global", "japan"}:
                self.gb_region.set(installation.region)
            self.installation_status.set(
                f"Detected {installation.label}. Metadata is ready."
            )
            self.save_settings(silent=True)
            self.status.set(f"Auto-detected {installation.label}")

        def failed(exc: Exception):
            self.installation_status.set(
                "Automatic detection did not complete. Run diagnostics or choose "
                "the paths manually."
            )
            self.status.set("Automatic game detection failed")
            if not automatic:
                messagebox.showerror(
                    "Could not auto-detect Umamusume", str(exc), parent=self.root
                )

        self._run_task(
            "Detecting Umamusume and preparing metadata…",
            lambda: detect_preferred_installation(self.region.get()),
            completed,
            failed=failed,
        )

    def choose_dat(self):
        path = filedialog.askdirectory(parent=self.root)
        if path:
            chosen = Path(path)
            if chosen.name.casefold() != "dat" and (chosen / "dat").is_dir():
                chosen /= "dat"
            self.dat_path.set(str(chosen))
            self.installation_status.set("Using manually selected game data.")
            self.save_settings(silent=True)

    def choose_meta(self):
        path = filedialog.askopenfilename(
            parent=self.root,
            filetypes=(("Database", "*.db meta*"), ("All", "*")),
        )
        if path:
            self.meta_path.set(path)
            self.installation_status.set("Using manually selected metadata.")
            self.save_settings(silent=True)

    def choose_game_dir(self):
        path = filedialog.askdirectory(parent=self.root)
        if path:
            self.game_dir.set(path)
            self.installation_status.set("Using manually selected game directory.")
            self.save_settings(silent=True)

    def save_settings(self, silent: bool = False):
        roots = [
            item.strip()
            for item in self.scan_roots.get().split(";")
            if item.strip()
        ]
        self.store.save_settings(
            {
                "profile": self.profile_name.get(),
                "dat_path": self.dat_path.get(),
                "meta_path": self.meta_path.get(),
                "game_dir": self.game_dir.get(),
                "region": self.region.get(),
                "gamebanana_region": self.gb_region.get(),
                "scan_roots": roots,
            }
        )
        if not silent:
            self.status.set("Settings saved")

    def open_manager_path(self, name: str):
        path = getattr(self.store.paths, name)
        path.mkdir(parents=True, exist_ok=True)
        open_path(path)

    def run_diagnostics(self):
        try:
            from umml_platform import format_doctor_report

            report, ready = format_doctor_report()
        except Exception as exc:
            report, ready = f"Diagnostics failed:\n{exc}", False
        window = tk.Toplevel(self.root)
        window.title("UMML diagnostics")
        window.geometry("820x560")
        box = tk.Text(
            window,
            wrap="none",
            background=SURFACE,
            foreground=TEXT,
            insertbackground=TEXT,
            font=("TkFixedFont", 10),
        )
        box.pack(fill="both", expand=True, padx=12, pady=12)
        box.insert("1.0", report)
        box.configure(state="disabled")
        self.status.set(
            "Diagnostics READY" if ready else "Diagnostics found incomplete setup"
        )

    def _refresh_game_status(self):
        try:
            running = running_game_processes(self.game_dir.get() or None)
            if running:
                self.game_status.set("Game running")
                self.game_badge.configure(style="Warning.Badge.TLabel")
            else:
                self.game_status.set("Game closed")
                self.game_badge.configure(style="Good.Badge.TLabel")
        except Exception:
            self.game_status.set("Game status unknown")
            self.game_badge.configure(style="Badge.TLabel")
        self.root.after(5000, self._refresh_game_status)

    def _run_task(
        self,
        label: str,
        operation: Callable[[], Any],
        completed: Callable[[Any], None],
        *,
        failed: Callable[[Exception], None] | None = None,
    ):
        if self._busy:
            if failed:
                failed(RuntimeError("Another UMML operation is still running."))
            else:
                messagebox.showinfo(
                    "UMML is busy",
                    "Another operation is still running.",
                    parent=self.root,
                )
            return
        self._busy = True
        self.status.set(label)
        self.progress.start(10)

        def worker():
            try:
                result = operation()
            except Exception as exc:
                self.root.after(
                    0,
                    lambda error=exc: self._task_failed(error, failed=failed),
                )
            else:
                self.root.after(
                    0,
                    lambda value=result: self._task_completed(value, completed),
                )

        threading.Thread(target=worker, daemon=True).start()

    def _task_completed(
        self,
        result: Any,
        completed: Callable[[Any], None],
    ):
        self._busy = False
        self.progress.stop()
        try:
            completed(result)
        except Exception as exc:
            self._task_failed(exc)

    def _task_failed(
        self,
        exc: Exception,
        *,
        failed: Callable[[Exception], None] | None = None,
    ):
        self._busy = False
        self.progress.stop()
        if failed:
            failed(exc)
            return
        self.status.set("Operation failed")
        messagebox.showerror("Operation failed", str(exc), parent=self.root)
