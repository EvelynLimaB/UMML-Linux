"""Game, Proton-prefix, and Umamusume data discovery."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterator, Mapping, Optional, Sequence

from .model import (
    DataCandidate, DiscoveryResult, GameCandidate, ProcessEvidence, SteamLibrary,
    _dedupe_data, _dedupe_games, absolute_no_resolve, find_child_casefold,
    path_variants, resolve_casefold_path, safe_is_dir, safe_is_file,
    valid_data_dir, GLOBAL_APP_ID, JAPAN_APP_ID, GLOBAL_DATA_FOLDER,
    JAPAN_DATA_FOLDER,
)
from .steam import (
    _env_path, _parse_int, discover_libraries, discover_steam_roots, scan_processes,
)
from .vdf import VDFError, get_casefold, load_vdf

def _manifest_state(path: Path) -> Optional[Mapping[str, object]]:
    try:
        parsed = load_vdf(path)
    except (OSError, VDFError, ValueError):
        return None
    state = get_casefold(parsed, "AppState")
    return state if isinstance(state, Mapping) else None


def _manifest_is_installed(state: Mapping[str, object]) -> bool:
    flags = _parse_int(get_casefold(state, "StateFlags"))
    return flags is None or not (flags & 1)


def _game_markers(app_id: int) -> tuple[str, tuple[str, ...]]:
    if app_id == GLOBAL_APP_ID:
        return GLOBAL_DATA_FOLDER, ("UmamusumePrettyDerby.exe", "umamusumeprettyderby.exe")
    return JAPAN_DATA_FOLDER, ("UmamusumePrettyDerby_Jpn.exe", "umamusumeprettyderby_jpn.exe")


def _looks_like_game(path: Path, app_id: int) -> bool:
    if not safe_is_dir(path):
        return False
    data_folder, executables = _game_markers(app_id)
    if safe_is_dir(find_child_casefold(path, data_folder)):
        return True
    try:
        names = {entry.name.casefold() for entry in path.iterdir()}
    except OSError:
        return False
    return any(name.casefold() in names for name in executables)


def _path_from_process_token(token: str) -> Optional[Path]:
    value = token.strip().strip('"').replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", value):
        if value[0].casefold() != "z":
            return None
        value = value[2:] or "/"
    return Path(value) if value.startswith("/") else None


def discover_game_candidates(
    app_id: int,
    libraries: Sequence[SteamLibrary],
    *,
    environ: Optional[Mapping[str, str]] = None,
    processes: Optional[Sequence[ProcessEvidence]] = None,
) -> list[GameCandidate]:
    environ = environ or os.environ
    processes = list(processes) if processes is not None else scan_processes()
    candidates: list[GameCandidate] = []

    override = environ.get(f"UMML_GAME_DIR_{app_id}")
    if not override and app_id == GLOBAL_APP_ID:
        override = environ.get("UMML_GAME_DIR")
    if override:
        path = Path(override).expanduser()
        if safe_is_dir(path):
            candidates.append(GameCandidate(absolute_no_resolve(path), "override", 1400))

    for process in processes:
        if process.app_id not in (None, app_id):
            continue
        process_score = 1250 if process.app_id == app_id else 900
        for key in ("STEAM_COMPAT_INSTALL_PATH", "STEAM_COMPAT_INSTALL_DIR"):
            value = _env_path(process.env, key)
            if value and _looks_like_game(value, app_id):
                candidates.append(GameCandidate(absolute_no_resolve(value), f"process:{process.pid}:{key}", process_score))
        values = [process.cwd, process.exe.parent if process.exe else None]
        values.extend(_path_from_process_token(token) for token in process.argv)
        for value in values:
            if value is None:
                continue
            for start in path_variants(value):
                for parent in (start, *start.parents):
                    if _looks_like_game(parent, app_id):
                        candidates.append(GameCandidate(absolute_no_resolve(parent), f"process:{process.pid}:path", process_score - 30))
                        break

    for library in libraries:
        manifest = library.steamapps / f"appmanifest_{app_id}.acf"
        if safe_is_file(manifest):
            state = _manifest_state(manifest)
            if state and _manifest_is_installed(state):
                manifest_app_id = _parse_int(get_casefold(state, "appid"))
                install_dir = get_casefold(state, "installdir")
                if (manifest_app_id in (None, app_id)) and install_dir:
                    common = find_child_casefold(library.steamapps, "common") or library.steamapps / "common"
                    path = resolve_casefold_path(common / str(install_dir))
                    if safe_is_dir(path):
                        candidates.append(
                            GameCandidate(
                                absolute_no_resolve(path),
                                f"manifest:{manifest}",
                                1150 + library.score // 20,
                                library.root,
                                manifest,
                            )
                        )

        common = find_child_casefold(library.steamapps, "common")
        if not common or not safe_is_dir(common):
            continue
        try:
            children = list(common.iterdir())
        except OSError:
            continue
        for child in children:
            if _looks_like_game(child, app_id):
                candidates.append(
                    GameCandidate(
                        absolute_no_resolve(child),
                        f"marker-scan:{common}",
                        850 + library.score // 25,
                        library.root,
                    )
                )
    return _dedupe_games(candidates)


def _prefix_modified(prefix: Path) -> float:
    for target in (prefix.parent / "pfx.lock", prefix, prefix.parent):
        try:
            return target.stat().st_mtime
        except OSError:
            continue
    return 0.0


def _locallow_candidates(prefix: Path, company: str, game: str) -> Iterator[Path]:
    users = prefix / "drive_c" / "users"
    if not safe_is_dir(users):
        return
    ordered: list[Path] = [users / "steamuser"]
    username = os.environ.get("USER") or os.environ.get("USERNAME")
    if username:
        ordered.append(users / username)
    try:
        ordered.extend(path for path in users.iterdir() if safe_is_dir(path))
    except OSError:
        pass
    seen: set[str] = set()
    for user in ordered:
        key = os.path.normcase(str(user))
        if key in seen:
            continue
        seen.add(key)
        candidate = user.joinpath("AppData", "LocalLow", company, game)
        if valid_data_dir(candidate):
            yield absolute_no_resolve(candidate)


def discover_data_candidates(
    app_id: int,
    libraries: Sequence[SteamLibrary],
    game_candidates: Sequence[GameCandidate],
    *,
    data_folder: str,
    company: str = "Cygames",
    game: str = "umamusume",
    environ: Optional[Mapping[str, str]] = None,
    processes: Optional[Sequence[ProcessEvidence]] = None,
) -> list[DataCandidate]:
    environ = environ or os.environ
    processes = list(processes) if processes is not None else scan_processes()
    candidates: list[DataCandidate] = []

    override = environ.get("UMML_PERSISTENT_DIR")
    if override:
        path = Path(override).expanduser()
        if valid_data_dir(path):
            candidates.append(DataCandidate(absolute_no_resolve(path), "override", 1500))

    for game_candidate in game_candidates:
        for game_path in path_variants(game_candidate.path):
            folder = find_child_casefold(game_path, data_folder)
            persistent = find_child_casefold(folder, "Persistent") if folder else None
            if persistent and valid_data_dir(persistent):
                candidates.append(
                    DataCandidate(
                        absolute_no_resolve(persistent),
                        f"game-local:{game_candidate.source}",
                        1300,
                        game_candidate.library,
                    )
                )

    prefix_paths: list[tuple[Path, str, int, Optional[Path]]] = []
    compat_override = environ.get("STEAM_COMPAT_DATA_PATH")
    if compat_override:
        compat = Path(compat_override).expanduser()
        prefix = compat / "pfx" if compat.name != "pfx" else compat
        prefix_paths.append((prefix, "environment:STEAM_COMPAT_DATA_PATH", 1450, None))

    for process in processes:
        if process.app_id not in (None, app_id):
            continue
        value = _env_path(process.env, "STEAM_COMPAT_DATA_PATH")
        if value:
            prefix = value / "pfx" if value.name != "pfx" else value
            prefix_paths.append((prefix, f"process:{process.pid}:STEAM_COMPAT_DATA_PATH", 1425, None))

    for library in libraries:
        compatdata = find_child_casefold(library.steamapps, "compatdata") or library.steamapps / "compatdata"
        app_dir = find_child_casefold(compatdata, str(app_id)) or compatdata / str(app_id)
        prefix = find_child_casefold(app_dir, "pfx") or app_dir / "pfx"
        if safe_is_dir(prefix):
            prefix_paths.append((prefix, f"library:{library.root}", 1100, library.root))

    seen_prefixes: set[str] = set()
    for prefix, source, score, library in prefix_paths:
        for variant in path_variants(prefix):
            key = os.path.normcase(str(variant))
            if key in seen_prefixes or not safe_is_dir(variant):
                continue
            seen_prefixes.add(key)
            modified = _prefix_modified(variant)
            for data in _locallow_candidates(variant, company, game):
                candidates.append(DataCandidate(data, source, score, library, variant, modified))
    return _dedupe_data(candidates)


def _same_library(game: GameCandidate, data: DataCandidate) -> bool:
    if not game.library or not data.library:
        return False
    try:
        return game.library.samefile(data.library)
    except OSError:
        return absolute_no_resolve(game.library) == absolute_no_resolve(data.library)


def choose_pair(
    games: Sequence[GameCandidate],
    data: Sequence[DataCandidate],
) -> tuple[Optional[Path], Optional[Path]]:
    pairs: list[tuple[int, float, GameCandidate, DataCandidate]] = []
    for game_candidate in games:
        if not safe_is_dir(game_candidate.path):
            continue
        for data_candidate in data:
            if not valid_data_dir(data_candidate.path):
                continue
            relation = 20 if _same_library(game_candidate, data_candidate) else 0
            pairs.append(
                (
                    game_candidate.score + data_candidate.score + relation,
                    data_candidate.modified,
                    game_candidate,
                    data_candidate,
                )
            )
    if not pairs:
        return None, None
    pairs.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return pairs[0][2].path, pairs[0][3].path


def discover_global_installation(
    *,
    home: Optional[Path] = None,
    environ: Optional[Mapping[str, str]] = None,
    processes: Optional[Sequence[ProcessEvidence]] = None,
) -> DiscoveryResult:
    environ = environ or os.environ
    processes = list(processes) if processes is not None else scan_processes()
    roots = discover_steam_roots(home=home, environ=environ, processes=processes)
    libraries = discover_libraries(roots, home=home)
    games = discover_game_candidates(GLOBAL_APP_ID, libraries, environ=environ, processes=processes)
    data = discover_data_candidates(
        GLOBAL_APP_ID,
        libraries,
        games,
        data_folder=GLOBAL_DATA_FOLDER,
        environ=environ,
        processes=processes,
    )
    game_dir, data_dir = choose_pair(games, data)
    notes: list[str] = []
    if not roots:
        notes.append("No Steam client root with a readable steamapps directory was found.")
    if roots and not libraries:
        notes.append("Steam roots were found, but no usable library was discovered.")
    if not games:
        notes.append("No installed Steam Global game candidate was found from overrides, processes, manifests, or marker scan.")
    if not data:
        notes.append("No valid game data containing both meta and dat was found in the game folder or Proton prefixes.")
    return DiscoveryResult(GLOBAL_APP_ID, game_dir, data_dir, games, data, roots, libraries, notes)


def manual_global_installation(
    selection: Path,
    data_selection: Optional[Path] = None,
    *,
    home: Optional[Path] = None,
    environ: Optional[Mapping[str, str]] = None,
    processes: Optional[Sequence[ProcessEvidence]] = None,
) -> DiscoveryResult:
    environ = dict(environ or os.environ)
    processes = list(processes) if processes is not None else scan_processes()
    game_dir: Optional[Path] = None
    selected_data: Optional[Path] = None

    def interpret(path: Path) -> tuple[Optional[Path], Optional[Path]]:
        for variant in path_variants(path):
            if variant.name == "dat" and valid_data_dir(variant.parent):
                return None, variant.parent
            if valid_data_dir(variant):
                if variant.name == "Persistent" and variant.parent.name.casefold().endswith("_data"):
                    return variant.parent.parent, variant
                return None, variant
            if variant.name == "Persistent":
                game = variant.parent.parent if variant.parent.name.casefold().endswith("_data") else None
                return game, variant
            if variant.name.casefold().endswith("_data"):
                return variant.parent, variant / "Persistent"
            folder = find_child_casefold(variant, GLOBAL_DATA_FOLDER)
            if folder or _looks_like_game(variant, GLOBAL_APP_ID):
                return variant, (folder / "Persistent") if folder else None
        return None, None

    game_dir, selected_data = interpret(selection)
    if data_selection is not None:
        alternate_game, alternate_data = interpret(data_selection)
        game_dir = game_dir or alternate_game
        if valid_data_dir(alternate_data):
            selected_data = alternate_data

    if game_dir:
        environ["UMML_GAME_DIR"] = str(game_dir)
    if valid_data_dir(selected_data):
        environ["UMML_PERSISTENT_DIR"] = str(selected_data)

    result = discover_global_installation(home=home, environ=environ, processes=processes)
    if game_dir and result.game_dir is None:
        result.game_dir = absolute_no_resolve(game_dir)
    if valid_data_dir(selected_data):
        result.data_dir = absolute_no_resolve(selected_data)
    return result


def format_discovery_report(result: DiscoveryResult) -> str:
    lines = [f"Steam autodetect report for app {result.app_id}"]
    lines.append("\nSteam roots:")
    for item in result.roots:
        lines.append(f"  [{item.score}] {item.path} ({item.source})")
    if not result.roots:
        lines.append("  none")

    lines.append("\nLibraries:")
    for item in result.libraries:
        lines.append(f"  [{item.score}] {item.root} -> {item.steamapps} ({item.source})")
    if not result.libraries:
        lines.append("  none")

    lines.append("\nGame candidates:")
    for item in result.game_candidates:
        marker = "OK" if safe_is_dir(item.path) else "MISSING"
        lines.append(f"  [{marker} {item.score}] {item.path} ({item.source})")
    if not result.game_candidates:
        lines.append("  none")

    lines.append("\nData candidates:")
    for item in result.data_candidates:
        marker = "OK" if valid_data_dir(item.path) else "INCOMPLETE"
        lines.append(f"  [{marker} {item.score}] {item.path} ({item.source})")
    if not result.data_candidates:
        lines.append("  none")

    lines.append("\nSelected:")
    lines.append(f"  game: {result.game_dir or 'none'}")
    lines.append(f"  data: {result.data_dir or 'none'}")
    for note in result.notes:
        lines.append(f"  note: {note}")
    lines.append(f"  result: {'READY' if result.ready else 'NOT READY'}")
    return "\n".join(lines)
