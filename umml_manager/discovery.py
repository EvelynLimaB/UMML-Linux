from __future__ import annotations

import os
import tarfile
import zipfile
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_METADATA = ("umml-mod.json", "setting.json", "setting.yml", "setting.yaml")
_ARCHIVES = (".zip", ".tar", ".tar.gz", ".tgz")
_SKIP_DIRS = {
    ".cache", ".git", ".hg", ".svn", "__pycache__", "node_modules",
    "steamapps", "compatdata", "shadercache", "venv", ".venv",
}


@dataclass(frozen=True)
class ModCandidate:
    path: Path
    kind: str
    name: str
    confidence: str
    reason: str


def default_search_roots() -> list[Path]:
    home = Path.home()
    roots = [home / "Downloads", home / "Documents", home / "Desktop"]
    xdg_download = os.environ.get("XDG_DOWNLOAD_DIR", "").strip().strip('"')
    if xdg_download:
        roots.insert(0, Path(os.path.expandvars(xdg_download)).expanduser())
    result: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root
        if resolved.is_dir() and resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


def is_mod_root(path: str | Path) -> bool:
    root = Path(path)
    has_metadata = any((root / name).is_file() for name in _METADATA)
    assets = root / "assets"
    has_assets = assets.is_dir() and _has_any_file(assets)
    hachimi = root / "hachimi"
    has_hachimi = hachimi.is_dir() and _has_any_file(hachimi)
    return has_metadata or has_assets or has_hachimi


def describe_mod_root(path: str | Path) -> ModCandidate | None:
    root = Path(path)
    markers = [name for name in _METADATA if (root / name).is_file()]
    assets = (root / "assets").is_dir() and _has_any_file(root / "assets")
    hachimi = (root / "hachimi").is_dir() and _has_any_file(root / "hachimi")
    if not (markers or assets or hachimi):
        return None
    if markers and assets:
        confidence = "high"
        reason = f"{markers[0]} and assets/"
    elif markers:
        confidence = "high"
        reason = markers[0]
    elif assets:
        confidence = "medium"
        reason = "assets/ with mod files"
    else:
        confidence = "medium"
        reason = "hachimi/ content"
    return ModCandidate(root, "folder", root.name, confidence, reason)


def scan_mod_candidates(
    roots: Iterable[str | Path],
    *,
    max_depth: int = 5,
    max_entries: int = 20_000,
    include_archives: bool = True,
) -> list[ModCandidate]:
    queue: deque[tuple[Path, int]] = deque()
    for value in roots:
        path = Path(value).expanduser()
        if path.is_dir():
            queue.append((path, 0))
    candidates: dict[Path, ModCandidate] = {}
    visited = 0
    while queue and visited < max_entries:
        current, depth = queue.popleft()
        visited += 1
        candidate = describe_mod_root(current)
        if candidate:
            candidates[current.resolve()] = candidate
            continue
        if depth >= max_depth:
            continue
        try:
            children = list(current.iterdir())
        except (OSError, PermissionError):
            continue
        for child in children:
            if child.is_dir():
                if child.name.casefold() in _SKIP_DIRS or child.name.startswith("."):
                    continue
                queue.append((child, depth + 1))
            elif include_archives and _archive_suffix(child):
                archive = describe_archive(child)
                if archive:
                    candidates[child.resolve()] = archive
    return sorted(candidates.values(), key=lambda item: (item.kind, item.name.casefold(), str(item.path)))


def locate_mod_root(path: str | Path, *, max_depth: int = 5) -> Path:
    selected = Path(path).expanduser().resolve()
    if is_mod_root(selected):
        return selected
    candidates = [item for item in scan_mod_candidates([selected], max_depth=max_depth, include_archives=False)]
    if not candidates:
        raise ValueError(f"No UMML-compatible mod folder found under {selected}")
    candidates.sort(key=lambda item: (len(item.path.relative_to(selected).parts), item.confidence != "high", str(item.path)))
    return candidates[0].path


def describe_archive(path: str | Path) -> ModCandidate | None:
    archive = Path(path)
    suffix = _archive_suffix(archive)
    if not suffix:
        return None
    reason = f"{suffix.lstrip('.').upper()} archive"
    confidence = "low"
    try:
        names: list[str] = []
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as package:
                names = [item.filename.replace("\\", "/") for item in package.infolist()[:3000]]
        elif tarfile.is_tarfile(archive):
            with tarfile.open(archive) as package:
                names = [item.name.replace("\\", "/") for item in package.getmembers()[:3000]]
        if names:
            base_names = {Path(name).name.casefold() for name in names}
            has_metadata = any(marker.casefold() in base_names for marker in _METADATA)
            has_assets = any("/assets/" in f"/{name.casefold().strip('/')}/" for name in names)
            if has_metadata or has_assets:
                confidence = "high" if has_metadata and has_assets else "medium"
                reason += " containing " + ("metadata and assets" if has_metadata and has_assets else "mod markers")
    except (OSError, tarfile.TarError, zipfile.BadZipFile):
        return None
    return ModCandidate(archive, "archive", archive.stem, confidence, reason)


def _archive_suffix(path: Path) -> str:
    lower = path.name.casefold()
    return next((suffix for suffix in _ARCHIVES if lower.endswith(suffix)), "")


def _has_any_file(root: Path) -> bool:
    try:
        return any(path.is_file() for path in root.rglob("*") if len(path.relative_to(root).parts) <= 4)
    except (OSError, PermissionError):
        return False
