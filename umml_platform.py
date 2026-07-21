"""Cross-platform game discovery and selection for UMML.

The module deliberately depends only on the Python standard library at import
time. The optional ``vdf`` package is imported lazily while reading Steam's
``libraryfolders.vdf`` so UMML can still show its normal dependency prompt.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

try:  # Windows-only module.
    import winreg  # type: ignore
except ImportError:  # pragma: no cover - expected on Linux/macOS.
    winreg = None

GLOBAL_STEAM_APP_ID = 3224770
JAPAN_STEAM_APP_ID = 3564400


@dataclass(frozen=True)
class GameInstallation:
    """A discovered UMML-compatible game installation."""

    key: str
    label: str
    region: str
    game_dir: Optional[Path]
    data_dir: Optional[Path]
    meta_path: Optional[Path]
    supported: bool = True
    note: str = ""

    @property
    def dat_path(self) -> Optional[Path]:
        if self.key == "komoe-tw":
            return self.game_dir / "dat" if self.game_dir else None
        return self.data_dir / "dat" if self.data_dir else None

    @property
    def backup_path(self) -> Optional[Path]:
        if self.key == "komoe-tw":
            return self.game_dir / "dat.backup" if self.game_dir else None
        return self.data_dir / "dat.backup" if self.data_dir else None

    @property
    def detected(self) -> bool:
        return bool(
            self.supported
            and self.game_dir
            and self.data_dir
            and self.meta_path
            and self.dat_path
            and self.game_dir.is_dir()
            and self.data_dir.is_dir()
            and self.meta_path.is_file()
            and self.dat_path.is_dir()
        )

    @property
    def status_text(self) -> str:
        if not self.supported:
            return "Not implemented"
        if self.detected:
            return "Detected"
        return "Not found"


def _path(value: object) -> Optional[Path]:
    if value is None:
        return None
    try:
        return Path(str(value)).expanduser()
    except (TypeError, ValueError, OSError):
        return None


def _unique_existing_dirs(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for candidate in paths:
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            resolved = candidate.expanduser()
        key = os.path.normcase(str(resolved))
        if resolved.is_dir() and key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def resolve_case_sensitive_path(path_obj: object) -> Optional[str]:
    """Resolve common Umamusume filename-case differences on Linux."""

    path = _path(path_obj)
    if path is None:
        return None
    if path.is_dir():
        return str(path)

    path_str = str(path)
    replacements = (
        ("umamusume", "Umamusume"),
        ("Umamusume", "umamusume"),
        ("umamusume_Data", "Umamusume_Data"),
        ("Umamusume_Data", "umamusume_Data"),
    )
    for old, new in replacements:
        alternate = Path(path_str.replace(old, new))
        if alternate != path and alternate.is_dir():
            print(f"Resolved case mismatch:\n{path}\n-> {alternate}")
            return str(alternate)
    return str(path)


def find_dmm_umamusume() -> Optional[str]:
    """Find the Japanese DMM install using DMM Game Player's config."""

    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    config_path = Path(appdata) / "dmmgameplayer5" / "dmmgame.cnf"
    if not config_path.is_file():
        return None

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            game_data = json.load(handle)
        for game in game_data.get("contents", []):
            if (
                game.get("productId") == "umamusume"
                and game.get("detail", {}).get("installed") is True
            ):
                install_path = _path(game.get("detail", {}).get("path"))
                if install_path and install_path.is_dir():
                    return str(install_path.resolve())
    except (OSError, ValueError, TypeError) as exc:
        print(f"DMM detection error: {exc}")
    return None


def find_komoe_umamusume() -> Optional[str]:
    """Find the Taiwan Komoe install from the Windows uninstall registry."""

    override = os.environ.get("UMML_KOMOE_GAME_DIR")
    override_path = _path(override)
    if override_path and override_path.is_dir():
        return str(override_path.resolve())

    if os.name != "nt" or winreg is None:
        return None
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\komoemumamusume",
        ) as key:
            display_icon = winreg.QueryValueEx(key, "DisplayIcon")[0]
        icon_path = str(display_icon).split(',', 1)[0].strip().strip('\"')
        candidate = Path(icon_path).parent / "komoemumamusume Game"
        if candidate.is_dir():
            return str(candidate.resolve())
    except (FileNotFoundError, OSError, TypeError) as exc:
        print(f"Komoe detection failed: {exc}")
    return None


def steam_root_candidates() -> list[str]:
    """Return native, Flatpak, Windows-registry and override Steam roots."""

    candidates: list[Path] = []
    override = _path(os.environ.get("UMML_STEAM_ROOT"))
    if override:
        candidates.append(override)

    if os.name == "nt" and winreg is not None:
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for key_path in (
                r"SOFTWARE\WOW6432Node\Valve\Steam",
                r"SOFTWARE\Valve\Steam",
            ):
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        candidates.append(Path(winreg.QueryValueEx(key, "InstallPath")[0]))
                except (FileNotFoundError, OSError, TypeError):
                    continue

    home = Path.home()
    candidates.extend(
        [
            home / ".local" / "share" / "Steam",
            home / ".steam" / "steam",
            home / ".steam" / "root",
            home
            / ".var"
            / "app"
            / "com.valvesoftware.Steam"
            / ".local"
            / "share"
            / "Steam",
        ]
    )

    # Common Windows defaults are useful when the registry is unavailable.
    for env_name in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
        base = os.environ.get(env_name)
        if base:
            candidates.append(Path(base) / "Steam")

    return [str(path) for path in _unique_existing_dirs(candidates)]


def get_steam_path() -> Optional[str]:
    roots = steam_root_candidates()
    return roots[0] if roots else None


def _load_vdf(path: Path) -> dict:
    import vdf  # Imported lazily; dependency handling belongs to UMML.py.

    with path.open("r", encoding="utf-8") as handle:
        return vdf.load(handle)


def get_steam_libraries(steam_path: Optional[str] = None) -> list[str]:
    """Read every Steam library, including secondary disks."""

    roots = [Path(steam_path)] if steam_path else [Path(p) for p in steam_root_candidates()]
    libraries: list[Path] = []

    for root in roots:
        libraries.append(root)
        vdf_path = root / "steamapps" / "libraryfolders.vdf"
        if not vdf_path.is_file():
            continue
        try:
            folders = _load_vdf(vdf_path).get("libraryfolders", {})
            for key, entry in folders.items():
                if not str(key).isdigit():
                    continue
                value = entry.get("path") if isinstance(entry, dict) else entry
                candidate = _path(value)
                if candidate:
                    libraries.append(candidate)
        except Exception as exc:  # Keep other Steam roots usable.
            print(f"Could not read Steam libraries from {vdf_path}: {exc}")

    return [str(path) for path in _unique_existing_dirs(libraries)]


def find_game_path(app_id: int) -> Optional[str]:
    """Find a Steam game's install directory from its app manifest."""

    override = os.environ.get(f"UMML_GAME_DIR_{app_id}")
    if not override and app_id == GLOBAL_STEAM_APP_ID:
        override = os.environ.get("UMML_GAME_DIR")
    override_path = _path(override)
    if override_path and override_path.is_dir():
        return str(override_path.resolve())

    for library in get_steam_libraries():
        manifest = Path(library) / "steamapps" / f"appmanifest_{app_id}.acf"
        if not manifest.is_file():
            continue
        try:
            app_state = _load_vdf(manifest).get("AppState", {})
            install_dir = app_state.get("installdir")
            if install_dir:
                candidate = Path(library) / "steamapps" / "common" / install_dir
                if candidate.is_dir():
                    return str(candidate.resolve())
        except Exception as exc:
            print(f"Could not parse {manifest}: {exc}")
    return None


def find_proton_locallow(
    app_id: int,
    company: str = "Cygames",
    game: str = "umamusume",
) -> Optional[Path]:
    """Find LocalLow game data inside a Steam Proton prefix."""

    override = _path(os.environ.get("UMML_PERSISTENT_DIR"))
    if override and override.is_dir():
        return override.resolve()

    for library in get_steam_libraries():
        users_root = (
            Path(library)
            / "steamapps"
            / "compatdata"
            / str(app_id)
            / "pfx"
            / "drive_c"
            / "users"
        )
        if not users_root.is_dir():
            continue
        users = [users_root / "steamuser"]
        try:
            users.extend(
                path
                for path in users_root.iterdir()
                if path.is_dir() and path.name != "steamuser"
            )
        except OSError:
            pass
        for user_dir in users:
            candidate = user_dir / "AppData" / "LocalLow" / company / game
            if (candidate / "meta").is_file():
                return candidate.resolve()
    return None


def _global_data_dir(game_dir: Optional[Path]) -> Optional[Path]:
    override = _path(os.environ.get("UMML_PERSISTENT_DIR"))
    if override and override.is_dir():
        return override.resolve()

    if game_dir:
        current = game_dir / "UmamusumePrettyDerby_Data" / "Persistent"
        if (current / "meta").is_file():
            return current.resolve()

    if os.name == "nt":
        old = Path.home() / "AppData" / "LocalLow" / "Cygames" / "umamusume"
        if (old / "meta").is_file():
            return old.resolve()
    else:
        proton = find_proton_locallow(GLOBAL_STEAM_APP_ID)
        if proton:
            return proton
    return None


def detect_installations() -> list[GameInstallation]:
    """Detect every game variant currently understood by UMML."""

    global_game = _path(find_game_path(GLOBAL_STEAM_APP_ID))
    global_data = _global_data_dir(global_game)

    japan_game = _path(find_game_path(JAPAN_STEAM_APP_ID))
    japan_data = (
        japan_game / "UmamusumePrettyDerby_Jpn_Data" / "Persistent"
        if japan_game
        else None
    )

    dmm_game = _path(find_dmm_umamusume())
    dmm_data = dmm_game / "umamusume_Data" / "Persistent" if dmm_game else None

    komoe_game = _path(find_komoe_umamusume())
    komoe_data = (
        komoe_game / "komoeumamusume_Data" / "Persistent"
        if komoe_game
        else None
    )

    return [
        GameInstallation(
            key="steam-global",
            label="Steam Global",
            region="Global",
            game_dir=global_game,
            data_dir=global_data,
            meta_path=global_data / "meta" if global_data else None,
            note="Steam app 3224770; native or Proton",
        ),
        GameInstallation(
            key="steam-japan",
            label="Steam Japan",
            region="Japan",
            game_dir=japan_game,
            data_dir=japan_data,
            meta_path=japan_data / "meta" if japan_data else None,
            note="Steam app 3564400",
        ),
        GameInstallation(
            key="dmm-japan",
            label="DMM Japan",
            region="Japan",
            game_dir=dmm_game,
            data_dir=dmm_data,
            meta_path=dmm_data / "meta" if dmm_data else None,
            note="Detected from DMM Game Player",
        ),
        GameInstallation(
            key="komoe-tw",
            label="Komoe Taiwan",
            region="Taiwan",
            game_dir=komoe_game,
            data_dir=komoe_data,
            meta_path=komoe_game / "meta" if komoe_game else None,
            note="Windows Komoe release",
        ),
        GameInstallation(
            key="kakao-kr",
            label="Kakao Korea",
            region="Korea",
            game_dir=None,
            data_dir=None,
            meta_path=None,
            supported=False,
            note="Upstream support is not implemented yet",
        ),
    ]


def _select_installation_dialog(
    parent: object,
    installations: list[GameInstallation],
) -> Optional[GameInstallation]:
    """Show a compact modal platform chooser using the existing Tk root."""

    import tkinter as tk
    from tkinter import ttk

    window = tk.Toplevel(parent)
    window.title("Choose Umamusume installation")
    window.transient(parent)
    window.resizable(True, False)
    window.minsize(620, 340)

    result: dict[str, Optional[GameInstallation]] = {"value": None}
    detected = [item for item in installations if item.detected]
    default = detected[0] if detected else installations[0]
    selected_key = tk.StringVar(value=default.key)

    outer = ttk.Frame(window, padding=20)
    outer.grid(row=0, column=0, sticky="nsew")
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)
    outer.columnconfigure(0, weight=1)

    ttk.Label(
        outer,
        text="Choose your game installation",
        style="Title.TLabel",
    ).grid(row=0, column=0, sticky="w")
    ttk.Label(
        outer,
        text="Detected installations are selected automatically. Missing versions remain visible for troubleshooting.",
        wraplength=570,
    ).grid(row=1, column=0, sticky="w", pady=(4, 14))

    list_frame = ttk.Frame(outer)
    list_frame.grid(row=2, column=0, sticky="ew")
    list_frame.columnconfigure(1, weight=1)

    for row, item in enumerate(installations):
        state = "normal" if item.supported else "disabled"
        ttk.Radiobutton(
            list_frame,
            variable=selected_key,
            value=item.key,
            state=state,
        ).grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=5)
        text_frame = ttk.Frame(list_frame)
        text_frame.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Label(text_frame, text=item.label, style="Choice.TLabel").pack(
            side="left"
        )
        ttk.Label(
            text_frame,
            text=f"  •  {item.status_text}",
            style="Detected.TLabel" if item.detected else "Muted.TLabel",
        ).pack(side="left")
        ttk.Label(
            list_frame,
            text=item.note,
            style="Muted.TLabel",
        ).grid(row=row, column=2, sticky="e", padx=(12, 0), pady=5)

    message = tk.StringVar(value="")
    ttk.Label(outer, textvariable=message, style="Error.TLabel").grid(
        row=3, column=0, sticky="w", pady=(12, 0)
    )

    buttons = ttk.Frame(outer)
    buttons.grid(row=4, column=0, sticky="e", pady=(16, 0))

    def cancel() -> None:
        result["value"] = None
        window.destroy()

    def accept() -> None:
        selected = next(
            (item for item in installations if item.key == selected_key.get()),
            None,
        )
        if selected is None or not selected.supported:
            message.set("That platform is not supported yet.")
            return
        if not selected.detected:
            message.set(
                "That installation was not detected. Run the game once or use the documented UMML_* path overrides."
            )
            return
        result["value"] = selected
        window.destroy()

    ttk.Button(buttons, text="Cancel", command=cancel).pack(side="left", padx=5)
    ttk.Button(buttons, text="Continue", command=accept, style="Accent.TButton").pack(
        side="left", padx=5
    )

    window.protocol("WM_DELETE_WINDOW", cancel)
    window.update_idletasks()
    try:
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - window.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - window.winfo_height()) // 2)
        window.geometry(f"+{x}+{y}")
    except Exception:
        pass
    window.grab_set()
    window.wait_window()
    return result["value"]


def load_settings(
    parent: object = None,
    status_callback: Optional[Callable[[str], None]] = None,
) -> tuple[str, str, str, str, str]:
    """Detect, select and validate an installation for UMML.

    Returns ``dat``, ``backup``, ``region``, ``game_dir`` and ``meta_path``.
    """

    def status(message: str) -> None:
        print(f"[Detection] {message}")
        if status_callback:
            status_callback(message)

    status("Searching Steam libraries and supported game installations…")
    installations = detect_installations()

    forced_key = os.environ.get("UMML_PLATFORM", "").strip().lower()
    if forced_key:
        selected = next((item for item in installations if item.key == forced_key), None)
        if selected is None:
            raise RuntimeError(
                f"Unknown UMML_PLATFORM={forced_key!r}. Expected one of: "
                + ", ".join(item.key for item in installations)
            )
    elif parent is not None:
        parent.deiconify()
        parent.lift()
        parent.update_idletasks()
        selected = _select_installation_dialog(parent, installations)
        if selected is None:
            raise SystemExit(0)
    else:
        selected = next((item for item in installations if item.detected), None)

    if selected is None:
        raise RuntimeError(
            "No supported Umamusume installation was detected. Run the game once, "
            "then use umml-doctor or the UMML_GAME_DIR / UMML_PERSISTENT_DIR overrides."
        )
    if not selected.supported:
        raise RuntimeError(f"{selected.label} support is not implemented yet.")
    if not selected.detected:
        raise RuntimeError(
            f"{selected.label} was selected but its game data is incomplete or missing."
        )

    assert selected.dat_path is not None
    assert selected.backup_path is not None
    assert selected.game_dir is not None
    assert selected.meta_path is not None

    status(f"Using {selected.label}: {selected.dat_path}")
    return (
        str(selected.dat_path),
        str(selected.backup_path),
        selected.region,
        str(selected.game_dir),
        str(selected.meta_path),
    )


def format_doctor_report() -> tuple[str, bool]:
    """Return a human-readable detection report and readiness flag."""

    lines = [
        "UMML platform doctor",
        f"Python: {sys.version.split()[0]}",
        f"Platform: {sys.platform} ({os.name})",
        f"Home: {Path.home()}",
        "",
        "Steam roots:",
    ]
    roots = steam_root_candidates()
    lines.extend(f"  [OK] {root}" for root in roots)
    if not roots:
        lines.append("  [FAIL] No native, Flatpak, or Windows Steam root detected.")

    lines.append("\nSteam libraries:")
    libraries = get_steam_libraries()
    lines.extend(f"  [OK] {library}" for library in libraries)
    if not libraries:
        lines.append("  [FAIL] No Steam libraries detected.")

    lines.append("\nGame installations:")
    installations = detect_installations()
    ready = False
    for item in installations:
        marker = "OK" if item.detected else "SKIP" if not item.supported else "CHECK"
        lines.append(f"  [{marker}] {item.label}: {item.status_text}")
        if item.game_dir:
            lines.append(f"      game: {item.game_dir}")
        if item.meta_path:
            lines.append(f"      meta: {item.meta_path}")
        if item.dat_path:
            lines.append(f"      dat: {item.dat_path}")
        if item.detected:
            writable = os.access(item.dat_path, os.W_OK) if item.dat_path else False
            lines.append(f"      writable: {'yes' if writable else 'NO'}")
            ready = ready or writable

    lines.append(f"\nRESULT: {'READY' if ready else 'NOT READY'}")
    if not ready:
        lines.append(
            "Launch the game once and let its data download finish. For unusual layouts, "
            "set UMML_GAME_DIR and UMML_PERSISTENT_DIR."
        )
    return "\n".join(lines), ready
