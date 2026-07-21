"""Shared models and filesystem helpers for UMML autodetection."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional

GLOBAL_APP_ID = 3224770
JAPAN_APP_ID = 3564400
GLOBAL_DATA_FOLDER = "UmamusumePrettyDerby_Data"
JAPAN_DATA_FOLDER = "UmamusumePrettyDerby_Jpn_Data"
GLOBAL_LOCALLOW = ("AppData", "LocalLow", "Cygames", "umamusume")


@dataclass(frozen=True)
class EvidencePath:
    path: Path
    source: str
    score: int


@dataclass(frozen=True)
class SteamLibrary:
    root: Path
    steamapps: Path
    source: str
    score: int


@dataclass(frozen=True)
class GameCandidate:
    path: Path
    source: str
    score: int
    library: Optional[Path] = None
    manifest: Optional[Path] = None


@dataclass(frozen=True)
class DataCandidate:
    path: Path
    source: str
    score: int
    library: Optional[Path] = None
    prefix: Optional[Path] = None
    modified: float = 0.0


@dataclass
class DiscoveryResult:
    app_id: int
    game_dir: Optional[Path]
    data_dir: Optional[Path]
    game_candidates: list[GameCandidate] = field(default_factory=list)
    data_candidates: list[DataCandidate] = field(default_factory=list)
    roots: list[EvidencePath] = field(default_factory=list)
    libraries: list[SteamLibrary] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return bool(self.game_dir and self.game_dir.is_dir() and valid_data_dir(self.data_dir))


@dataclass(frozen=True)
class ProcessEvidence:
    pid: int
    app_id: Optional[int]
    env: Mapping[str, str]
    cwd: Optional[Path]
    exe: Optional[Path]
    argv: tuple[str, ...]


class VDFError(ValueError):
    pass


def absolute_no_resolve(path: Path) -> Path:
    try:
        return path.expanduser().absolute()
    except OSError:
        return path.expanduser()


def path_variants(path: Path) -> list[Path]:
    values = [absolute_no_resolve(path)]
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        resolved = None
    if resolved is not None and resolved != values[0]:
        values.append(resolved)
    return values


def safe_is_dir(path: Optional[Path]) -> bool:
    if path is None:
        return False
    try:
        return path.is_dir()
    except OSError:
        return False


def safe_is_file(path: Optional[Path]) -> bool:
    if path is None:
        return False
    try:
        return path.is_file()
    except OSError:
        return False


def valid_data_dir(path: Optional[Path]) -> bool:
    return bool(path and safe_is_dir(path) and safe_is_file(path / "meta") and safe_is_dir(path / "dat"))


def _identity_key(path: Path) -> str:
    try:
        identity = path.expanduser().resolve()
    except OSError:
        identity = absolute_no_resolve(path)
    return os.path.normcase(str(identity))


def _dedupe_evidence(items: Iterable[EvidencePath]) -> list[EvidencePath]:
    best: dict[str, EvidencePath] = {}
    for item in items:
        path = absolute_no_resolve(item.path)
        key = _identity_key(path)
        candidate = EvidencePath(path, item.source, item.score)
        if key not in best or candidate.score > best[key].score:
            best[key] = candidate
    return sorted(best.values(), key=lambda item: (-item.score, str(item.path)))


def _dedupe_libraries(items: Iterable[SteamLibrary]) -> list[SteamLibrary]:
    best: dict[str, SteamLibrary] = {}
    for item in items:
        key = _identity_key(item.steamapps)
        if key not in best or item.score > best[key].score:
            best[key] = item
    return sorted(best.values(), key=lambda item: (-item.score, str(item.root)))


def _dedupe_games(items: Iterable[GameCandidate]) -> list[GameCandidate]:
    best: dict[str, GameCandidate] = {}
    for item in items:
        key = _identity_key(item.path)
        if key not in best or item.score > best[key].score:
            best[key] = item
    return sorted(best.values(), key=lambda item: (-item.score, str(item.path)))


def _dedupe_data(items: Iterable[DataCandidate]) -> list[DataCandidate]:
    best: dict[str, DataCandidate] = {}
    for item in items:
        key = _identity_key(item.path)
        previous = best.get(key)
        if previous is None or (item.score, item.modified) > (previous.score, previous.modified):
            best[key] = item
    return sorted(best.values(), key=lambda item: (-item.score, -item.modified, str(item.path)))


def find_child_casefold(parent: Path, name: str) -> Optional[Path]:
    exact = parent / name
    if safe_is_dir(exact) or safe_is_file(exact):
        return exact
    try:
        matches = [entry for entry in parent.iterdir() if entry.name.casefold() == name.casefold()]
    except OSError:
        return None
    if not matches:
        return None
    matches.sort(key=lambda entry: (entry.name != name, entry.name.casefold(), entry.name))
    return matches[0]


def find_steamapps(root: Path) -> Optional[Path]:
    for variant in path_variants(root):
        if variant.name.casefold() == "steamapps" and safe_is_dir(variant):
            return variant
        child = find_child_casefold(variant, "steamapps")
        if child and safe_is_dir(child):
            return child
    return None


def resolve_casefold_path(path: Path) -> Path:
    path = path.expanduser()
    if path.exists():
        return absolute_no_resolve(path)
    if not path.is_absolute():
        path = absolute_no_resolve(path)
    parts = path.parts
    if not parts:
        return path
    current = Path(parts[0])
    for part in parts[1:]:
        exact = current / part
        if exact.exists():
            current = exact
            continue
        found = find_child_casefold(current, part)
        if found is None:
            return path
        current = found
    return absolute_no_resolve(current)
