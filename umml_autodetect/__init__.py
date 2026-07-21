"""Robust Steam and Proton autodetection for UMML."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

from .model import (
    DataCandidate, DiscoveryResult, EvidencePath, GameCandidate, ProcessEvidence,
    SteamLibrary, VDFError, GLOBAL_APP_ID, JAPAN_APP_ID, GLOBAL_DATA_FOLDER,
    JAPAN_DATA_FOLDER, valid_data_dir,
)
from .vdf import parse_vdf_text
from .steam import discover_libraries, discover_steam_roots, scan_processes
from .game import (
    discover_global_installation, format_discovery_report,
    manual_global_installation,
)

__all__ = [
    "DataCandidate", "DiscoveryResult", "EvidencePath", "GameCandidate",
    "ProcessEvidence", "SteamLibrary", "VDFError", "GLOBAL_APP_ID",
    "JAPAN_APP_ID", "GLOBAL_DATA_FOLDER", "JAPAN_DATA_FOLDER",
    "discover_global_installation", "discover_libraries",
    "discover_steam_roots", "format_discovery_report",
    "manual_global_installation", "parse_vdf_text", "scan_processes",
    "valid_data_dir", "apply",
]


def apply() -> None:
    """Integrate the discovery engine with UMML's existing platform/UI layer."""

    # Preserve the mature upstream registry-based behavior on Windows.
    if os.name == "nt":
        return

    import umml_platform as platform

    if getattr(platform, "_UMML_AUTODETECT_V2", False):
        return
    platform._UMML_AUTODETECT_V2 = True

    original_detect = platform.detect_installations
    original_doctor = platform.format_doctor_report
    original_load_settings = platform.load_settings
    original_find_game = platform.find_game_path

    cache: dict[str, DiscoveryResult] = {}

    def result(refresh: bool = False) -> DiscoveryResult:
        if refresh or "global" not in cache:
            cache["global"] = discover_global_installation()
        return cache["global"]

    def steam_root_candidates() -> list[str]:
        return [str(item.path) for item in result().roots]

    def get_steam_libraries(steam_path: Optional[str] = None) -> list[str]:
        if steam_path:
            roots = [EvidencePath(Path(steam_path), "explicit", 1500)]
            return [str(item.root) for item in discover_libraries(roots)]
        return [str(item.root) for item in result().libraries]

    def find_game_path(app_id: int) -> Optional[str]:
        if app_id == GLOBAL_APP_ID:
            current = result()
            return str(current.game_dir) if current.game_dir else None
        return original_find_game(app_id)

    def find_proton_locallow(
        app_id: int,
        company: str = "Cygames",
        game: str = "umamusume",
    ) -> Optional[Path]:
        if app_id == GLOBAL_APP_ID:
            return result().data_dir
        return None

    def global_data_dir(game_dir: Optional[Path]) -> Optional[Path]:
        current = result()
        if current.data_dir:
            return current.data_dir
        if game_dir:
            direct = game_dir / GLOBAL_DATA_FOLDER / "Persistent"
            if valid_data_dir(direct):
                return direct
        return None

    def detect_installations():
        current = result()
        installations = original_detect()
        for index, item in enumerate(installations):
            if item.key != "steam-global":
                continue
            note_parts = ["Steam app 3224770"]
            if current.game_candidates:
                note_parts.append(current.game_candidates[0].source)
            if current.data_candidates:
                note_parts.append(current.data_candidates[0].source)
            installations[index] = platform.GameInstallation(
                key=item.key,
                label=item.label,
                region=item.region,
                game_dir=current.game_dir,
                data_dir=current.data_dir,
                meta_path=current.data_dir / "meta" if current.data_dir else None,
                supported=item.supported,
                note="; ".join(note_parts),
            )
        return installations

    def manual_dialog(parent) -> Optional[tuple[str, str, str, str, str]]:
        from tkinter import filedialog, messagebox

        if not messagebox.askyesno(
            "Automatic detection did not finish",
            "UMML could not pair the Steam Global game with valid data automatically.\n\n"
            "Locate either the game folder or the data folder manually?",
            parent=parent,
        ):
            return None
        selection = filedialog.askdirectory(
            parent=parent,
            title="Locate Umamusume game root, Persistent, LocalLow data, or dat",
            mustexist=True,
        )
        if not selection:
            return None
        current = manual_global_installation(Path(selection))
        if not current.ready:
            second = messagebox.askyesno(
                "One half is still missing",
                "UMML found only the game or only its data.\n\nLocate the other folder now?",
                parent=parent,
            )
            if second:
                other = filedialog.askdirectory(
                    parent=parent,
                    title="Locate the remaining game or data folder",
                    mustexist=True,
                )
                if other:
                    current = manual_global_installation(Path(selection), Path(other))
        if not current.ready:
            messagebox.showerror(
                "Installation still incomplete",
                format_discovery_report(current),
                parent=parent,
            )
            return None
        assert current.game_dir and current.data_dir
        return (
            str(current.data_dir / "dat"),
            str(current.data_dir / "dat.backup"),
            "Global",
            str(current.game_dir),
            str(current.data_dir / "meta"),
        )

    def load_settings(
        parent=None,
        status_callback: Optional[Callable[[str], None]] = None,
    ):
        current = result(refresh=True)
        installations = detect_installations()
        detected = [item for item in installations if item.detected]
        if (
            current.ready
            and not os.environ.get("UMML_PLATFORM")
            and len(detected) == 1
            and detected[0].key == "steam-global"
        ):
            if status_callback:
                status_callback(f"Automatically detected Steam Global: {current.data_dir}")
            assert current.game_dir and current.data_dir
            return (
                str(current.data_dir / "dat"),
                str(current.data_dir / "dat.backup"),
                "Global",
                str(current.game_dir),
                str(current.data_dir / "meta"),
            )
        if parent is not None and not detected:
            manual = manual_dialog(parent)
            if manual:
                return manual
        return original_load_settings(parent=parent, status_callback=status_callback)

    def doctor():
        current = result(refresh=True)
        text, ready = original_doctor()
        return text + "\n\n" + format_discovery_report(current), ready or current.ready

    platform.steam_root_candidates = steam_root_candidates
    platform.get_steam_libraries = get_steam_libraries
    platform.get_steam_path = lambda: steam_root_candidates()[0] if steam_root_candidates() else None
    platform.find_game_path = find_game_path
    platform.find_proton_locallow = find_proton_locallow
    platform._global_data_dir = global_data_dir
    platform.detect_installations = detect_installations
    platform.load_settings = load_settings
    platform.format_doctor_report = doctor
