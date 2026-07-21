#!/usr/bin/env python3
"""Runtime Steam-detection fixes for packaged UMML Linux builds.

The module patches ``umml_platform`` before UMML imports its public helpers. It
is intentionally small and removable once the same fixes are accepted upstream.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, Optional

import umml_platform as platform

_APPLIED = False
_ORIGINALS: dict[str, object] = {}


def _unique_dirs(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for value in paths:
        try:
            path = value.expanduser().resolve()
            exists = path.is_dir()
        except OSError:
            continue
        key = os.path.normcase(str(path))
        if exists and key not in seen:
            seen.add(key)
            result.append(path)
    return result


def _steam_root_from_path(value: Path) -> Optional[Path]:
    try:
        value = value.expanduser().resolve()
    except OSError:
        value = value.expanduser()
    try:
        current = value if value.is_dir() else value.parent
    except OSError:
        current = value.parent
    for candidate in (current, *current.parents):
        try:
            if candidate.name == "steamapps" and candidate.parent.is_dir():
                return candidate.parent
            if (candidate / "steamapps").is_dir():
                return candidate
        except OSError:
            continue
    return None


def _process_path(token: str) -> Optional[Path]:
    token = token.strip().strip('"').replace(chr(92), "/")
    if re.match(r"^[A-Za-z]:/", token):
        drive, rest = token[0].upper(), token[2:]
        if drive != "Z":
            return None
        token = rest or "/"
    return Path(token) if token.startswith("/") else None


def _running_process_paths() -> list[Path]:
    if os.name == "nt" or not Path("/proc").is_dir():
        return []
    result: list[Path] = []
    try:
        processes = list(Path("/proc").iterdir())
    except OSError:
        return result
    needles = ("steam", "proton", "umamusume", "3224770", "3564400")
    for process in processes:
        if not process.name.isdigit():
            continue
        try:
            raw = (process / "cmdline").read_bytes()
        except OSError:
            continue
        command = raw.replace(b"\0", b" ").decode("utf-8", errors="replace").lower()
        if not any(needle in command for needle in needles):
            continue
        for link_name in ("cwd", "exe"):
            try:
                result.append((process / link_name).resolve())
            except OSError:
                pass
        for token in raw.decode("utf-8", errors="replace").split("\0"):
            path = _process_path(token)
            if path is not None:
                result.append(path)
    return result


def _extra_steam_roots() -> list[Path]:
    home = Path.home()
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    candidates = [
        home / ".steam" / "debian-installation",
        xdg_data / "Steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
        home / "snap" / "steam" / "common" / ".local" / "share" / "Steam",
        home / "snap" / "steam" / "common" / ".steam" / "steam",
    ]
    for name in ("STEAM_COMPAT_CLIENT_INSTALL_PATH", "STEAM_ROOT", "STEAM_DIR"):
        value = os.environ.get(name)
        if value:
            candidates.append(Path(value))
    for process_path in _running_process_paths():
        root = _steam_root_from_path(process_path)
        if root is not None:
            candidates.append(root)
    return _unique_dirs(candidates)


def _decode_vdf(value: str) -> str:
    slash = chr(92)
    return value.replace(slash * 2, slash).replace(slash + '"', '"')


def _fallback_vdf(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.name.startswith("appmanifest_"):
        match = re.search(r'"installdir"\s*"((?:\\.|[^"\\])*)"', text, re.I)
        return {"AppState": {"installdir": _decode_vdf(match.group(1)) if match else None}}
    folders: dict[str, dict[str, str]] = {}
    for index, match in enumerate(re.finditer(r'"path"\s*"((?:\\.|[^"\\])*)"', text, re.I)):
        folders[str(index)] = {"path": _decode_vdf(match.group(1))}
    return {"libraryfolders": folders}


def _known_names(app_id: int) -> tuple[str, ...]:
    if app_id == platform.GLOBAL_STEAM_APP_ID:
        return ("Umamusume Pretty Derby", "UmamusumePrettyDerby", "Uma Global")
    if app_id == platform.JAPAN_STEAM_APP_ID:
        return ("Umamusume Pretty Derby Jpn", "UmamusumePrettyDerby_Jpn", "Uma Japan")
    return ()


def _running_game_dirs(app_id: int) -> list[Path]:
    result: list[Path] = []
    data_name = "UmamusumePrettyDerby_Data" if app_id == platform.GLOBAL_STEAM_APP_ID else "UmamusumePrettyDerby_Jpn_Data"
    normalized_names = tuple(name.lower().replace(" ", "") for name in _known_names(app_id))
    for value in _running_process_paths():
        text = str(value).lower().replace(" ", "")
        if str(app_id) not in text and not any(name in text for name in normalized_names):
            continue
        start = value if value.suffix == "" else value.parent
        for candidate in (start, *start.parents):
            try:
                if (candidate / data_name).is_dir():
                    result.append(candidate)
                    break
            except OSError:
                continue
    return _unique_dirs(result)


def _library_from_game(game_dir: Path) -> Optional[Path]:
    for candidate in (game_dir, *game_dir.parents):
        if candidate.name == "common" and candidate.parent.name == "steamapps":
            return candidate.parent.parent
    return _steam_root_from_path(game_dir)


def _proton_data_from_game(game_dir: Path) -> Optional[Path]:
    library = _library_from_game(game_dir)
    if library is None:
        return None
    users = library / "steamapps" / "compatdata" / str(platform.GLOBAL_STEAM_APP_ID) / "pfx" / "drive_c" / "users"
    if not users.is_dir():
        return None
    candidates = [users / "steamuser"]
    try:
        candidates.extend(path for path in users.iterdir() if path.is_dir())
    except OSError:
        pass
    for user in candidates:
        data = user / "AppData" / "LocalLow" / "Cygames" / "umamusume"
        if (data / "meta").is_file():
            return data.resolve()
    return None


def _manual_global(game_dir: Path) -> Optional[platform.GameInstallation]:
    game_dir = game_dir.expanduser().resolve()
    if game_dir.name == "Persistent":
        game_dir = game_dir.parent.parent
    elif game_dir.name.endswith("_Data"):
        game_dir = game_dir.parent
    data = game_dir / "UmamusumePrettyDerby_Data" / "Persistent"
    if not (data / "meta").is_file():
        data = _proton_data_from_game(game_dir) or data
    item = platform.GameInstallation(
        key="steam-global",
        label="Steam Global",
        region="Global",
        game_dir=game_dir,
        data_dir=data,
        meta_path=data / "meta",
        note="Manually selected game folder",
    )
    return item if item.detected else None


def apply() -> None:
    global _APPLIED
    if _APPLIED:
        return
    _APPLIED = True

    original_roots = platform.steam_root_candidates
    original_load_vdf = platform._load_vdf
    original_find_game = platform.find_game_path
    original_global_data = platform._global_data_dir
    original_load_settings = platform.load_settings
    _ORIGINALS.update(roots=original_roots, load_vdf=original_load_vdf, find_game=original_find_game, global_data=original_global_data, load_settings=original_load_settings)

    def roots() -> list[str]:
        combined = [Path(value) for value in original_roots()]
        combined.extend(_extra_steam_roots())
        return [str(path) for path in _unique_dirs(combined)]

    def load_vdf(path: Path) -> dict:
        try:
            return original_load_vdf(path)
        except Exception as exc:
            print(f"Using packaged Valve KeyValues fallback for {path}: {exc}")
            return _fallback_vdf(path)

    def find_game(app_id: int) -> Optional[str]:
        found = original_find_game(app_id)
        if found:
            return found
        running = _running_game_dirs(app_id)
        if running:
            return str(running[0])
        for library in platform.get_steam_libraries():
            common = Path(library) / "steamapps" / "common"
            for name in _known_names(app_id):
                candidate = common / name
                if candidate.is_dir():
                    return str(candidate.resolve())
        return None

    def global_data(game_dir: Optional[Path]) -> Optional[Path]:
        found = original_global_data(game_dir)
        if found or game_dir is None:
            return found
        return _proton_data_from_game(game_dir)

    def load_settings(parent=None, status_callback=None):
        installations = platform.detect_installations()
        if parent is not None and not any(item.detected for item in installations):
            from tkinter import filedialog, messagebox
            locate = messagebox.askyesno(
                "Automatic detection failed",
                "UMML could not identify the running Steam installation.\n\nLocate the Steam Global game folder manually?",
                parent=parent,
            )
            if locate:
                chosen = filedialog.askdirectory(parent=parent, title="Locate Umamusume Pretty Derby game folder", mustexist=True)
                if chosen:
                    item = _manual_global(Path(chosen))
                    if item is not None:
                        assert item.dat_path and item.backup_path and item.meta_path and item.game_dir
                        return (str(item.dat_path), str(item.backup_path), item.region, str(item.game_dir), str(item.meta_path))
                    messagebox.showerror("Incompatible folder", "Select the folder containing UmamusumePrettyDerby_Data.", parent=parent)
        return original_load_settings(parent=parent, status_callback=status_callback)

    platform.steam_root_candidates = roots
    platform._load_vdf = load_vdf
    platform.find_game_path = find_game
    platform._global_data_dir = global_data
    platform.load_settings = load_settings

    def status_text(item) -> str:
        if not item.supported:
            return "Not implemented"
        if item.detected:
            return "Detected"
        if item.game_dir and item.game_dir.is_dir():
            return "Game found; data missing"
        if item.data_dir and item.data_dir.is_dir():
            return "Data found; game missing"
        return "Not found"

    platform.GameInstallation.status_text = property(status_text)
