"""Safety guards for the legacy one-folder UMML interface.

This module deliberately does not turn legacy UMML into a multi-mod manager.
It only prevents the most dangerous operations while the game is running and
replaces the broken per-mod unload action with the existing full restore flow.
"""

from __future__ import annotations

import csv
import os
import subprocess
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Iterable, Iterator


@dataclass(frozen=True)
class RunningProcess:
    pid: int
    name: str
    command: str = ""


_MUTATING_METHODS = (
    "load_assets",
    "load_assets_manual",
    "restore_original_assets",
    "delete_master_db",
    "clean_unused_assets",
    "force_translate_english",
)


def _iter_procfs() -> Iterator[RunningProcess]:
    proc = Path("/proc")
    if not proc.is_dir():
        return
    current = os.getpid()
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == current:
            continue
        try:
            name = (entry / "comm").read_text(encoding="utf-8", errors="replace").strip()
            raw = (entry / "cmdline").read_bytes().replace(b"\0", b" ")
            command = raw.decode("utf-8", errors="replace").strip()
        except (OSError, PermissionError):
            continue
        yield RunningProcess(pid=pid, name=name, command=command)


def _iter_windows_tasks() -> Iterator[RunningProcess]:
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return
    if result.returncode:
        return
    for row in csv.reader(result.stdout.splitlines()):
        if len(row) < 2:
            continue
        try:
            pid = int(row[1].replace(",", ""))
        except ValueError:
            continue
        yield RunningProcess(pid=pid, name=row[0], command=row[0])


def iter_processes() -> Iterable[RunningProcess]:
    if os.name == "nt":
        return tuple(_iter_windows_tasks())
    return tuple(_iter_procfs())


def process_looks_like_game(process: RunningProcess, game_dir: str | Path | None = None) -> bool:
    name = process.name.casefold()
    command = process.command.casefold()
    if "umamusume" in name or "umamusume" in Path(name).stem:
        return True
    if "umamusume.exe" in command:
        return True
    if game_dir:
        try:
            resolved = str(Path(game_dir).expanduser().resolve()).casefold()
        except OSError:
            resolved = str(Path(game_dir).expanduser()).casefold()
        if resolved and resolved in command and (".exe" in command or "unity" in command):
            return True
    return False


def find_game_processes(game_dir: str | Path | None = None) -> tuple[RunningProcess, ...]:
    return tuple(process for process in iter_processes() if process_looks_like_game(process, game_dir))


def _warn_game_running(gui, operation: str, processes: tuple[RunningProcess, ...]) -> None:
    from tkinter import messagebox

    names = ", ".join(sorted({process.name for process in processes})) or "UM:PD"
    messagebox.showwarning(
        "Close the game first",
        f"UMML blocked '{operation}' because the game appears to be running ({names}).\n\n"
        "You may prepare or download mods while playing, but legacy UMML must only "
        "write, restore, clean, or delete game data after the game has fully closed.",
        parent=getattr(gui, "root", None),
    )


def _guard_method(gui_class, method_name: str) -> None:
    original = getattr(gui_class, method_name, None)
    if not callable(original) or getattr(original, "_umml_game_guard", False):
        return

    @wraps(original)
    def guarded(self, *args, **kwargs):
        processes = find_game_processes(getattr(self, "game_dir", None))
        if processes:
            _warn_game_running(self, method_name.replace("_", " "), processes)
            return None
        return original(self, *args, **kwargs)

    guarded._umml_game_guard = True  # type: ignore[attr-defined]
    setattr(gui_class, method_name, guarded)


def _install_safe_unload(gui_class) -> None:
    original = getattr(gui_class, "unload_assets", None)
    if not callable(original) or getattr(original, "_umml_safe_unload", False):
        return

    def safe_unload(self, *args, **kwargs):
        from tkinter import messagebox

        processes = find_game_processes(getattr(self, "game_dir", None))
        if processes:
            _warn_game_running(self, "unload assets", processes)
            return None
        messagebox.showinfo(
            "Legacy unload replaced",
            "Legacy UMML cannot safely reconstruct one mod from a shared backup. "
            "The old unload implementation could crash or restore the wrong state.\n\n"
            "UMML will open the existing original-asset restore tool instead. "
            "Per-mod enable/disable belongs to the separate UMML Manager.",
            parent=getattr(self, "root", None),
        )
        return self.restore_original_assets()

    safe_unload._umml_safe_unload = True  # type: ignore[attr-defined]
    setattr(gui_class, "unload_assets", safe_unload)


def install_legacy_safety(gui_class) -> None:
    """Patch one GUI class once with conservative legacy-mode safety behavior."""

    if getattr(gui_class, "_umml_legacy_safety_installed", False):
        return
    for method_name in _MUTATING_METHODS:
        _guard_method(gui_class, method_name)
    _install_safe_unload(gui_class)
    gui_class._umml_legacy_safety_installed = True
