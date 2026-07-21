from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .discovery import is_mod_root, locate_mod_root
from .models import ModRecord, Profile, SourceSpec


class StoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class ManagerPaths:
    root: Path
    registry: Path
    sources: Path
    prepared: Path
    profiles: Path
    settings: Path
    workspaces: Path
    state: Path
    baseline: Path
    transactions: Path

    @classmethod
    def at(cls, root: str | Path) -> "ManagerPaths":
        root = Path(root).expanduser()
        return cls(
            root=root,
            registry=root / "mods.json",
            sources=root / "sources",
            prepared=root / "prepared",
            profiles=root / "profiles.json",
            settings=root / "settings.json",
            workspaces=root / "workspaces",
            state=root / "active.json",
            baseline=root / "baseline",
            transactions=root / "transactions",
        )


class ManagerStore:
    def __init__(self, root: str | Path):
        self.paths = ManagerPaths.at(root)
        self.paths.root.mkdir(parents=True, exist_ok=True)

    def list_mods(self) -> list[ModRecord]:
        data = _read_json(self.paths.registry, {"mods": []})
        return [ModRecord.from_dict(item) for item in data.get("mods", [])]

    def get_mod(self, mod_id: str) -> ModRecord:
        for record in self.list_mods():
            if record.id == mod_id:
                return record
        raise StoreError(f"Unknown mod: {mod_id}")

    def save_mod(self, record: ModRecord) -> None:
        mods = {item.id: item for item in self.list_mods()}
        mods[record.id] = record
        _write_json(self.paths.registry, {"version": 1, "mods": [mods[key].to_dict() for key in sorted(mods)]})

    def remove_mod(self, mod_id: str) -> None:
        mods = [record for record in self.list_mods() if record.id != mod_id]
        _write_json(self.paths.registry, {"version": 1, "mods": [record.to_dict() for record in mods]})

    def list_profiles(self) -> list[Profile]:
        data = _read_json(self.paths.profiles, {"profiles": [{"name": "Default", "enabled": []}]})
        return [Profile.from_dict(item) for item in data.get("profiles", [])]

    def get_profile(self, name: str) -> Profile:
        for profile in self.list_profiles():
            if profile.name == name:
                return profile
        raise StoreError(f"Unknown profile: {name}")

    def save_profile(self, profile: Profile) -> None:
        profiles = {item.name: item for item in self.list_profiles()}
        profiles[profile.name] = profile
        _write_json(self.paths.profiles,{"version":1,"profiles":[profiles[key].to_dict() for key in sorted(profiles)]})

    def load_settings(self) -> dict[str, Any]:
        return dict(_read_json(self.paths.settings, {}))

    def save_settings(self, values: dict[str, Any]) -> None:
        current = self.load_settings()
        current.update(values)
        _write_json(self.paths.settings, current)

    def import_folder(self, folder: str | Path, *, mod_id: str | None = None, source: SourceSpec | None = None) -> ModRecord:
        folder = Path(folder).expanduser().resolve()
        if not folder.is_dir():
            raise StoreError(f"Mod folder not found: {folder}")
        if not is_mod_root(folder):
            try:
                folder = locate_mod_root(folder)
            except ValueError as exc:
                raise StoreError(str(exc)) from exc
        metadata = read_mod_metadata(folder)
        chosen_id = sanitize_id(mod_id or metadata.get("id") or metadata.get("title") or folder.name)
        version = str(metadata.get("mod_version") or metadata.get("version") or "0")
        destination = self.paths.sources / chosen_id / version
        _copy_tree_atomic(folder, destination)
        record = ModRecord(id=chosen_id, name=str(metadata.get("title") or chosen_id), version=version, description=str(metadata.get("description") or ""), author=str(metadata.get("author") or metadata.get("submitter") or ""), regions=_regions(metadata), source=source or SourceSpec(), source_path=str(destination), imported_at=_now())
        self.save_mod(record)
        return record

    def import_archive(self, archive: str | Path, *, mod_id: str | None = None, source: SourceSpec | None = None) -> ModRecord:
        archive = Path(archive).expanduser().resolve()
        if not archive.is_file():
            raise StoreError(f"Archive not found: {archive}")
        temp = Path(tempfile.mkdtemp(prefix="umml-import-", dir=self.paths.root))
        try:
            extract_archive(archive, temp)
            root = find_mod_root(temp)
            return self.import_folder(root, mod_id=mod_id, source=source)
        finally:
            shutil.rmtree(temp, ignore_errors=True)

    def create_workspace(self, mod_id: str) -> Path:
        record = self.get_mod(mod_id)
        source = Path(record.source_path)
        if not source.is_dir():
            raise StoreError(f"Source files are missing for {record.name}")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        destination = self.paths.workspaces / mod_id / stamp
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination)
        marker = {"base_mod_id":record.id,"base_version":record.version,"created_at":_now(),"instructions":"Edit this copy, then import the workspace as a new local mod version."}
        (destination / ".umml-workspace.json").write_text(json.dumps(marker,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        return destination


def default_root() -> Path:
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "umml-manager"


def sanitize_id(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", value.casefold()).strip("-.")
    if not cleaned:
        raise StoreError("Could not derive a stable mod ID")
    return cleaned[:96]


def read_mod_metadata(root: Path) -> dict[str, Any]:
    for name in ("umml-mod.json", "setting.json"):
        path = root / name
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
            except (OSError, json.JSONDecodeError) as exc:
                raise StoreError(f"Invalid {name}: {exc}") from exc
    for name in ("setting.yml", "setting.yaml"):
        yaml_path = root / name
        if yaml_path.is_file():
            try:
                import yaml
                data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
                return data if isinstance(data,dict) else {}
            except Exception as exc:
                raise StoreError(f"Invalid {name}: {exc}") from exc
    return {"title":root.name,"mod_version":"0"}


def find_mod_root(extracted: Path) -> Path:
    if is_mod_root(extracted):
        return extracted
    try:
        return locate_mod_root(extracted,max_depth=8)
    except ValueError as exc:
        raise StoreError("Archive has no recognizable UMML/Hachimi mod folder") from exc


def extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True,exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as package:
            for member in package.infolist():
                _safe_member(member.filename)
                if ((member.external_attr >> 16) & 0o170000) == 0o120000:
                    raise StoreError(f"Archive symlink rejected: {member.filename}")
            package.extractall(destination)
        return
    if tarfile.is_tarfile(archive):
        with tarfile.open(archive) as package:
            members = package.getmembers()
            for member in members:
                _safe_member(member.name)
                if member.issym() or member.islnk() or member.isdev():
                    raise StoreError(f"Archive link/device rejected: {member.name}")
            package.extractall(destination,members=members)
        return
    raise StoreError("Unsupported archive; use ZIP or TAR")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member(name: str) -> PurePosixPath:
    normalized = name.replace("\\","/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise StoreError(f"Unsafe archive path rejected: {name!r}")
    if path.parts and ":" in path.parts[0]:
        raise StoreError(f"Unsafe archive path rejected: {name!r}")
    return path


def _copy_tree_atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True,exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{destination.name}-",dir=destination.parent))
    try:
        shutil.copytree(source,temp/"content",dirs_exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        (temp/"content").replace(destination)
    finally:
        shutil.rmtree(temp,ignore_errors=True)


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(temp,path)


def _regions(metadata: dict[str, Any]) -> list[str]:
    value = metadata.get("regions",metadata.get("region",[]))
    if isinstance(value,str):
        return [value]
    if isinstance(value,list):
        return [str(item) for item in value]
    return []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
