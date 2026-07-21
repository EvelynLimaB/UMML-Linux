from __future__ import annotations

import csv
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    name: str
    command: str


def running_game_processes(game_dir: str | Path | None = None) -> tuple[ProcessInfo, ...]:
    game = str(Path(game_dir).expanduser()).casefold() if game_dir else ""
    found: list[ProcessInfo] = []
    for process in _iter_processes():
        text = f"{process.name} {process.command}".casefold()
        if "umamusume" in text or (game and game in text and ".exe" in text):
            found.append(process)
    return tuple(found)


def _iter_processes() -> Iterable[ProcessInfo]:
    if os.name == "nt":
        return tuple(_windows_processes())
    return tuple(_procfs_processes())


def _procfs_processes() -> Iterable[ProcessInfo]:
    proc = Path("/proc")
    if not proc.is_dir():
        return ()
    found: list[ProcessInfo] = []
    for entry in proc.iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            name = (entry / "comm").read_text(errors="replace").strip()
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        found.append(ProcessInfo(int(entry.name), name, command))
    return found


def _windows_processes() -> Iterable[ProcessInfo]:
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ()
    if result.returncode:
        return ()
    found: list[ProcessInfo] = []
    for row in csv.reader(result.stdout.splitlines()):
        if len(row) < 2:
            continue
        try:
            pid = int(row[1].replace(",", ""))
        except ValueError:
            continue
        found.append(ProcessInfo(pid, row[0], row[0]))
    return found
