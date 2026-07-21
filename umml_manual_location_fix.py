#!/usr/bin/env python3
"""Repair manual Steam Global selection for symlinked Mint installations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import umml_detection_hotfix as hotfix
import umml_platform as platform

_APPLIED = False


def _absolute(path: Path) -> Path:
    try:
        return path.expanduser().absolute()
    except OSError:
        return path.expanduser()


def _variants(path: Path) -> list[Path]:
    values = [_absolute(path)]
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        resolved = None
    if resolved is not None and resolved != values[0]:
        values.append(resolved)
    return values


def _valid_data(path: Optional[Path]) -> bool:
    if path is None:
        return False
    try:
        return path.is_dir() and (path / "meta").is_file() and (path / "dat").is_dir()
    except OSError:
        return False


def _game_and_data(selection: Path) -> tuple[Optional[Path], Optional[Path]]:
    for selected in _variants(selection):
        if selected.name == "dat" and _valid_data(selected.parent):
            return None, selected.parent
        if _valid_data(selected):
            if selected.name == "Persistent" and selected.parent.name.endswith("_Data"):
                return selected.parent.parent, selected
            return None, selected
        if selected.name == "Persistent":
            game = selected.parent.parent if selected.parent.name.endswith("_Data") else None
            return game, selected
        if selected.name.endswith("_Data"):
            return selected.parent, selected / "Persistent"
        data_folder = selected / "UmamusumePrettyDerby_Data"
        if data_folder.is_dir() or (selected / "UmamusumePrettyDerby.exe").is_file():
            return selected, data_folder / "Persistent"
    return None, None


def _library_from_unresolved_game(game_dir: Path) -> Optional[Path]:
    for variant in _variants(game_dir):
        for parent in (variant, *variant.parents):
            if parent.name == "common" and parent.parent.name == "steamapps":
                return parent.parent.parent
    return None


def _all_libraries(game_dir: Optional[Path]) -> list[Path]:
    values: list[Path] = []
    if game_dir is not None:
        library = _library_from_unresolved_game(game_dir)
        if library is not None:
            values.append(library)
    try:
        values.extend(Path(value) for value in platform.get_steam_libraries())
    except Exception as exc:
        print(f"Could not enumerate Steam libraries: {exc}")

    result: list[Path] = []
    seen: set[str] = set()
    for value in values:
        for path in _variants(value):
            key = str(path)
            try:
                exists = path.is_dir()
            except OSError:
                exists = False
            if exists and key not in seen:
                seen.add(key)
                result.append(path)
    return result


def _find_proton_data(game_dir: Optional[Path]) -> Optional[Path]:
    for library in _all_libraries(game_dir):
        users = (
            library
            / "steamapps"
            / "compatdata"
            / str(platform.GLOBAL_STEAM_APP_ID)
            / "pfx"
            / "drive_c"
            / "users"
        )
        if not users.is_dir():
            continue
        candidates = [users / "steamuser"]
        try:
            candidates.extend(path for path in users.iterdir() if path.is_dir())
        except OSError:
            pass
        for user in candidates:
            data = user / "AppData" / "LocalLow" / "Cygames" / "umamusume"
            if _valid_data(data):
                return _absolute(data)
    return None


def _manual_global(
    selection: Path,
    data_selection: Optional[Path] = None,
) -> Optional[platform.GameInstallation]:
    game_dir, data_dir = _game_and_data(selection)

    if data_selection is not None:
        selected_game, selected_data = _game_and_data(data_selection)
        if game_dir is None:
            game_dir = selected_game
        if _valid_data(selected_data):
            data_dir = selected_data

    if game_dir is not None and not _valid_data(data_dir):
        for variant in _variants(game_dir):
            direct = variant / "UmamusumePrettyDerby_Data" / "Persistent"
            if _valid_data(direct):
                data_dir = direct
                break

    if not _valid_data(data_dir):
        data_dir = _find_proton_data(game_dir)

    if game_dir is None:
        try:
            found = platform.find_game_path(platform.GLOBAL_STEAM_APP_ID)
        except Exception:
            found = None
        if found:
            game_dir = Path(found)

    if game_dir is None or not _valid_data(data_dir):
        return None

    item = platform.GameInstallation(
        key="steam-global",
        label="Steam Global",
        region="Global",
        game_dir=game_dir,
        data_dir=data_dir,
        meta_path=data_dir / "meta",
        note="Manually selected installation",
    )
    return item if item.detected else None


def apply() -> None:
    global _APPLIED
    if _APPLIED:
        return
    _APPLIED = True

    hotfix._manual_global = _manual_global
    base_load_settings = hotfix._ORIGINALS.get("load_settings", platform.load_settings)

    def load_settings(parent=None, status_callback=None):
        installations = platform.detect_installations()
        if parent is not None and not any(item.detected for item in installations):
            from tkinter import filedialog, messagebox

            if messagebox.askyesno(
                "Automatic detection failed",
                "UMML could not identify Steam Global automatically.\n\n"
                "Locate the game folder manually?",
                parent=parent,
            ):
                chosen_game = filedialog.askdirectory(
                    parent=parent,
                    title="Locate the folder containing UmamusumePrettyDerby_Data",
                    mustexist=True,
                )
                item = _manual_global(Path(chosen_game)) if chosen_game else None

                if item is None and chosen_game and messagebox.askyesno(
                    "Game folder found; data folder missing",
                    "The game folder is valid, but its Proton data is elsewhere.\n\n"
                    "Locate the folder containing both 'meta' and 'dat'?",
                    parent=parent,
                ):
                    chosen_data = filedialog.askdirectory(
                        parent=parent,
                        title="Locate Persistent or LocalLow/Cygames/umamusume",
                        mustexist=True,
                    )
                    if chosen_data:
                        item = _manual_global(Path(chosen_game), Path(chosen_data))

                if item is not None:
                    assert item.dat_path and item.backup_path and item.meta_path and item.game_dir
                    return (
                        str(item.dat_path),
                        str(item.backup_path),
                        item.region,
                        str(item.game_dir),
                        str(item.meta_path),
                    )

                if chosen_game:
                    messagebox.showerror(
                        "Could not validate the installation",
                        "The game folder was accepted, but UMML still could not find a data folder "
                        "containing both 'meta' and 'dat'.",
                        parent=parent,
                    )

        return base_load_settings(parent=parent, status_callback=status_callback)

    platform.load_settings = load_settings
