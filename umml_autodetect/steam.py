"""Steam client roots and library discovery."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .model import (
    EvidencePath, ProcessEvidence, SteamLibrary, VDFError,
    _dedupe_evidence, _dedupe_libraries, absolute_no_resolve,
    find_steamapps, path_variants, resolve_casefold_path, safe_is_dir, safe_is_file,
    GLOBAL_APP_ID, JAPAN_APP_ID,
)
from .vdf import get_casefold, load_vdf, walk_casefold_keys

def _parse_int(value: object) -> Optional[int]:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _process_app_id(env: Mapping[str, str], argv: Sequence[str]) -> Optional[int]:
    for key in ("SteamAppId", "SteamGameId", "STEAM_APP_ID", "STEAM_GAME_ID"):
        app_id = _parse_int(env.get(key))
        if app_id:
            return app_id
    joined = " ".join(argv)
    for app_id in (GLOBAL_APP_ID, JAPAN_APP_ID):
        if str(app_id) in joined:
            return app_id
    return None


def scan_processes(proc_root: Path = Path("/proc")) -> list[ProcessEvidence]:
    if os.name == "nt" or not safe_is_dir(proc_root):
        return []
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return []
    result: list[ProcessEvidence] = []
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            raw_env = (entry / "environ").read_bytes()
            env: dict[str, str] = {}
            for item in raw_env.split(b"\0"):
                if b"=" not in item:
                    continue
                key, value = item.split(b"=", 1)
                env[key.decode(errors="replace")] = value.decode(errors="replace")
        except OSError:
            env = {}
        try:
            raw_cmd = (entry / "cmdline").read_bytes()
            argv = tuple(
                token.decode("utf-8", errors="replace")
                for token in raw_cmd.split(b"\0")
                if token
            )
        except OSError:
            argv = ()
        app_id = _process_app_id(env, argv)
        command = " ".join(argv).casefold()
        relevant = app_id in (GLOBAL_APP_ID, JAPAN_APP_ID) or any(
            needle in command for needle in ("umamusume", "proton", "steam")
        )
        if not relevant:
            continue
        try:
            cwd = (entry / "cwd").resolve()
        except OSError:
            cwd = None
        try:
            exe = (entry / "exe").resolve()
        except OSError:
            exe = None
        result.append(ProcessEvidence(int(entry.name), app_id, env, cwd, exe, argv))
    return result


def _env_path(environ: Mapping[str, str], name: str) -> Optional[Path]:
    value = environ.get(name)
    return Path(value).expanduser() if value else None


def discover_steam_roots(
    *,
    home: Optional[Path] = None,
    environ: Optional[Mapping[str, str]] = None,
    processes: Optional[Sequence[ProcessEvidence]] = None,
) -> list[EvidencePath]:
    home = home or Path.home()
    environ = environ or os.environ
    processes = list(processes) if processes is not None else scan_processes()
    candidates: list[EvidencePath] = []

    for key, score in (
        ("UMML_STEAM_ROOT", 1200),
        ("STEAM_DIR", 1150),
        ("STEAM_ROOT", 1100),
        ("STEAM_COMPAT_CLIENT_INSTALL_PATH", 1100),
    ):
        value = _env_path(environ, key)
        if value:
            candidates.append(EvidencePath(value, f"environment:{key}", score))

    compat_data = _env_path(environ, "STEAM_COMPAT_DATA_PATH")
    if compat_data:
        for parent in (compat_data, *compat_data.parents):
            if parent.name.casefold() == "compatdata" and parent.parent.name.casefold() == "steamapps":
                candidates.append(EvidencePath(parent.parent.parent, "environment:STEAM_COMPAT_DATA_PATH", 1125))
                break

    defaults = (
        (".steam/debian-installation", 940, "native-debian"),
        (".local/share/Steam", 930, "native-xdg"),
        (".local/share/steam", 925, "native-xdg-lowercase"),
        (".steam/steam", 920, "native-legacy"),
        (".steam/root", 915, "native-root-link"),
        (".steam", 880, "native-parent"),
        (".var/app/com.valvesoftware.Steam/.local/share/Steam", 910, "flatpak-current"),
        (".var/app/com.valvesoftware.Steam/.local/share/steam", 905, "flatpak-current-lowercase"),
        (".var/app/com.valvesoftware.Steam/data/Steam", 890, "flatpak-legacy"),
        (".var/app/com.valvesoftware.Steam/data/steam", 885, "flatpak-legacy-lowercase"),
        ("snap/steam/common/.local/share/Steam", 880, "snap"),
        (".snap/data/steam/common/.local/share/Steam", 875, "snap-hidden"),
    )
    for relative, score, source in defaults:
        candidates.append(EvidencePath(home / relative, source, score))
    for path, score, source in (
        (Path("/usr/share/steam"), 700, "system"),
        (Path("/usr/local/share/steam"), 690, "system-local"),
    ):
        candidates.append(EvidencePath(path, source, score))

    for process in processes:
        process_score = 1060 if process.app_id in (GLOBAL_APP_ID, JAPAN_APP_ID) else 800
        for key in ("STEAM_COMPAT_CLIENT_INSTALL_PATH", "STEAM_DIR", "STEAM_ROOT"):
            value = _env_path(process.env, key)
            if value:
                candidates.append(EvidencePath(value, f"process:{process.pid}:{key}", process_score))
        process_compat = _env_path(process.env, "STEAM_COMPAT_DATA_PATH")
        if process_compat:
            for parent in (process_compat, *process_compat.parents):
                if parent.name.casefold() == "compatdata" and parent.parent.name.casefold() == "steamapps":
                    candidates.append(EvidencePath(parent.parent.parent, f"process:{process.pid}:compatdata", process_score + 10))
                    break
        for value in (process.cwd, process.exe):
            if value:
                for parent in (value, *value.parents):
                    steamapps = find_steamapps(parent)
                    if steamapps:
                        candidates.append(EvidencePath(steamapps.parent, f"process:{process.pid}:path", process_score - 50))
                        break

    validated: list[EvidencePath] = []
    for candidate in _dedupe_evidence(candidates):
        steamapps = find_steamapps(candidate.path)
        if steamapps:
            validated.append(EvidencePath(steamapps.parent, candidate.source, candidate.score))
    return _dedupe_evidence(validated)


def _flatpak_translate(root: Path, configured: Path, home: Path) -> Path:
    text = str(root)
    if ".var/app/com.valvesoftware.Steam" not in text:
        return configured
    native_xdg = home / ".local" / "share" / "Steam"
    native_xdg_lower = home / ".local" / "share" / "steam"
    if configured in (native_xdg, native_xdg_lower):
        return root
    return configured


def discover_libraries(
    roots: Sequence[EvidencePath],
    *,
    home: Optional[Path] = None,
) -> list[SteamLibrary]:
    home = home or Path.home()
    libraries: list[SteamLibrary] = []
    for root_evidence in roots:
        steamapps = find_steamapps(root_evidence.path)
        if not steamapps:
            continue
        libraries.append(SteamLibrary(steamapps.parent, steamapps, root_evidence.source, root_evidence.score))

        configs = [steamapps / "libraryfolders.vdf", root_evidence.path / "config" / "libraryfolders.vdf"]
        for config in configs:
            if not safe_is_file(config):
                continue
            try:
                parsed = load_vdf(config)
                folder_map = get_casefold(parsed, "libraryfolders", {})
                if not isinstance(folder_map, Mapping):
                    continue
                for key, entry in folder_map.items():
                    if not str(key).isdigit():
                        continue
                    mounted = None
                    if isinstance(entry, Mapping):
                        value = get_casefold(entry, "path")
                        mounted = get_casefold(entry, "mounted")
                    else:
                        value = entry
                    if not value:
                        continue
                    configured = Path(str(value)).expanduser()
                    configured = _flatpak_translate(root_evidence.path, configured, home)
                    configured = resolve_casefold_path(configured)
                    configured_steamapps = find_steamapps(configured)
                    if configured_steamapps:
                        score = root_evidence.score - (15 if str(mounted) == "0" else 5)
                        libraries.append(
                            SteamLibrary(
                                configured_steamapps.parent,
                                configured_steamapps,
                                f"{root_evidence.source}:{config.name}",
                                score,
                            )
                        )
            except (OSError, VDFError, ValueError):
                continue

        config_vdf = root_evidence.path / "config" / "config.vdf"
        if safe_is_file(config_vdf):
            try:
                parsed = load_vdf(config_vdf)
                for value in walk_casefold_keys(parsed, "baseinstallfolder_"):
                    if not value:
                        continue
                    configured = resolve_casefold_path(Path(str(value)).expanduser())
                    configured_steamapps = find_steamapps(configured)
                    if configured_steamapps:
                        libraries.append(
                            SteamLibrary(
                                configured_steamapps.parent,
                                configured_steamapps,
                                f"{root_evidence.source}:config.vdf",
                                root_evidence.score - 10,
                            )
                        )
            except (OSError, VDFError, ValueError):
                pass
    return _dedupe_libraries(libraries)
