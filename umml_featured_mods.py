"""Opt-in third-party downloads with reversible, conflict-aware installs.

Featured archives are downloaded unchanged from their publisher after consent;
they are never included in UMML release artifacts.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable

DARK_MODE_ID = "umpd-dark-mode"
DARK_MODE_TITLE = "UM:PD Dark Mode"
DARK_MODE_GAMEBANANA_FILE_ID = 1743782
DARK_MODE_SOURCE_URL = "https://gamebanana.com/mods/665326"
DARK_MODE_LICENSE_NAME = "CC BY-NC-ND 4.0"
DARK_MODE_LICENSE_URL = "https://creativecommons.org/licenses/by-nc-nd/4.0/"
DARK_MODE_API_URL = (
    "https://gamebanana.com/apiv11/Mod/665326"
    "?_csvProperties=_sName,_aSubmitter,_aFiles"
)
DARK_MODE_FALLBACK_DOWNLOAD_URL = "https://gamebanana.com/dl/1743782"
USER_AGENT = (
    "UMML-Linux featured-mod downloader/1.0 "
    "(+https://github.com/EvelynLimaB/UMML-Linux)"
)


class FeaturedModError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModMetadata:
    title: str
    author: str
    source_url: str
    license_name: str
    license_url: str
    file_id: int
    file_name: str
    download_url: str


@dataclass(frozen=True)
class InstallResult:
    changed: int
    skipped: int = 0
    conflicts: tuple[str, ...] = ()


Progress = Callable[[str], None]
Decrypt = Callable[..., tuple[int, int]]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _xdg(name: str, fallback: Path) -> Path:
    return Path(os.environ.get(name, fallback)).expanduser()


def default_state_root() -> Path:
    return _xdg("XDG_STATE_HOME", Path.home() / ".local/state") / "umml"


def default_cache_root() -> Path:
    return _xdg("XDG_CACHE_HOME", Path.home() / ".cache") / "umml"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else dict(default)
    except (OSError, ValueError, TypeError):
        return dict(default)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        temporary = Path(stream.name)
    temporary.replace(path)


def _as_id(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _file_records(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, list):
        yield from (item for item in value if isinstance(item, dict))
    elif isinstance(value, dict):
        if any(key in value for key in ("_sDownloadUrl", "_sFile", "_idRow")):
            yield value
        for item in value.values():
            if isinstance(item, (list, dict)):
                yield from _file_records(item)


def _author(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("_sName", "name", "_sUsername", "username"):
            if value.get(key):
                return str(value[key])
    return str(value) if value else "GameBanana submitter"


def _header_filename(headers: Any, fallback: str) -> str:
    value = headers.get("Content-Disposition", "") if headers else ""
    parameters: dict[str, str] = {}
    for part in value.split(";")[1:]:
        if "=" in part:
            key, item = part.split("=", 1)
            parameters[key.strip().lower()] = item.strip()
    encoded = parameters.get("filename*")
    if encoded:
        return Path(urllib.parse.unquote(encoded.split("''", 1)[-1])).name or fallback
    plain = parameters.get("filename")
    return Path(plain.strip('"')).name if plain else fallback


class GameBananaClient:
    def __init__(self, timeout: int = 45):
        self.timeout = timeout

    @staticmethod
    def _request(url: str) -> urllib.request.Request:
        return urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json, application/octet-stream;q=0.9, */*;q=0.8",
            },
        )

    def fetch_metadata(self) -> ModMetadata:
        title = DARK_MODE_TITLE
        author = "GameBanana submitter"
        name = f"gamebanana-{DARK_MODE_GAMEBANANA_FILE_ID}.download"
        download = DARK_MODE_FALLBACK_DOWNLOAD_URL
        try:
            with urllib.request.urlopen(
                self._request(DARK_MODE_API_URL), timeout=self.timeout
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, dict):
                title = str(payload.get("_sName") or title)
                author = _author(payload.get("_aSubmitter"))
                records = list(_file_records(payload.get("_aFiles")))
                selected = next(
                    (
                        item
                        for item in records
                        if DARK_MODE_GAMEBANANA_FILE_ID
                        in {
                            _as_id(item.get("_idRow")),
                            _as_id(item.get("_id")),
                            _as_id(item.get("id")),
                            _as_id(item.get("_idFile")),
                        }
                    ),
                    records[0] if records else None,
                )
                if selected:
                    name = str(selected.get("_sFile") or selected.get("_sFileName") or name)
                    download = str(
                        selected.get("_sDownloadUrl")
                        or selected.get("_sUrl")
                        or download
                    )
                    if download.startswith("//"):
                        download = "https:" + download
                    elif download.startswith("/"):
                        download = urllib.parse.urljoin(DARK_MODE_SOURCE_URL, download)
        except (OSError, ValueError, TypeError, urllib.error.URLError):
            pass
        return ModMetadata(
            title,
            author,
            DARK_MODE_SOURCE_URL,
            DARK_MODE_LICENSE_NAME,
            DARK_MODE_LICENSE_URL,
            DARK_MODE_GAMEBANANA_FILE_ID,
            Path(name).name,
            download,
        )

    def download(
        self,
        metadata: ModMetadata,
        destination: Path,
        progress: Progress | None = None,
    ) -> Path:
        destination.mkdir(parents=True, exist_ok=True)
        fallback = metadata.file_name or f"gamebanana-{metadata.file_id}.download"
        cached = destination / fallback
        if cached.is_file() and cached.stat().st_size:
            return cached
        if progress:
            progress("Downloading the original archive from GameBanana…")
        try:
            with urllib.request.urlopen(
                self._request(metadata.download_url), timeout=self.timeout
            ) as response:
                output = destination / _header_filename(response.headers, fallback)
                with tempfile.NamedTemporaryFile("wb", dir=destination, delete=False) as stream:
                    temporary = Path(stream.name)
                    shutil.copyfileobj(response, stream, 1024 * 1024)
        except (OSError, urllib.error.URLError) as exc:
            raise FeaturedModError(f"Could not download {metadata.title}: {exc}") from exc
        if not temporary.stat().st_size:
            temporary.unlink(missing_ok=True)
            raise FeaturedModError("GameBanana returned an empty download.")
        temporary.replace(output)
        return output


def _safe_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name.replace("\\", "/"))
    if not name or path.is_absolute() or ".." in path.parts:
        raise FeaturedModError(f"Unsafe archive path rejected: {name!r}")
    if path.parts and ":" in path.parts[0]:
        raise FeaturedModError(f"Unsafe archive path rejected: {name!r}")
    return path


def _extract_zip(archive: Path, target: Path) -> None:
    with zipfile.ZipFile(archive) as package:
        for item in package.infolist():
            _safe_path(item.filename)
            if ((item.external_attr >> 16) & 0o170000) == 0o120000:
                raise FeaturedModError(f"Archive link rejected: {item.filename}")
        package.extractall(target)


def _extract_tar(archive: Path, target: Path) -> None:
    with tarfile.open(archive) as package:
        for item in package.getmembers():
            _safe_path(item.name)
            if item.issym() or item.islnk() or item.isdev():
                raise FeaturedModError(f"Archive link/device rejected: {item.name}")
        package.extractall(target)


def _extract_7z(archive: Path, target: Path) -> None:
    executable = shutil.which("7zz") or shutil.which("7z")
    if not executable:
        raise FeaturedModError(
            "This is a 7z archive. Install '7zip' or 'p7zip-full', then try again."
        )
    listing = subprocess.run(
        [executable, "l", "-slt", str(archive)], capture_output=True, text=True
    )
    if listing.returncode:
        raise FeaturedModError(listing.stderr.strip() or "7z could not inspect the archive.")
    for line in listing.stdout.splitlines():
        if line.startswith("Path = "):
            value = line[7:].strip()
            if value and Path(value).name != archive.name:
                _safe_path(value)
    result = subprocess.run(
        [executable, "x", "-y", f"-o{target}", str(archive)],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise FeaturedModError(result.stderr.strip() or "7z could not extract the archive.")


def extract_archive(archive: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="extract-", dir=destination.parent))
    try:
        if zipfile.is_zipfile(archive):
            _extract_zip(archive, temporary)
        elif tarfile.is_tarfile(archive):
            _extract_tar(archive, temporary)
        else:
            with archive.open("rb") as stream:
                is_7z = stream.read(6) == b"7z\xbc\xaf\x27\x1c"
            if not is_7z:
                raise FeaturedModError("Download is not a supported ZIP, TAR, or 7z archive.")
            _extract_7z(archive, temporary)
        if destination.exists():
            shutil.rmtree(destination)
        temporary.replace(destination)
        return destination
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def find_mod_root(extracted: Path) -> Path:
    candidates: list[tuple[int, int, Path]] = []
    for assets in extracted.rglob("assets"):
        if assets.is_dir():
            root = assets.parent
            settings = int((root / "setting.json").is_file() or (root / "setting.yml").is_file())
            candidates.append((-settings, len(root.relative_to(extracted).parts), root))
    if not candidates:
        raise FeaturedModError("Archive has no UMML-compatible assets folder.")
    return sorted(candidates, key=lambda item: (item[0], item[1], str(item[2])))[0][2]


class FeaturedModManager:
    def __init__(
        self,
        dat_path: str | Path,
        decrypt_assets: Decrypt,
        state_root: str | Path | None = None,
        cache_root: str | Path | None = None,
        client: GameBananaClient | None = None,
    ):
        self.dat_path = Path(dat_path)
        state = Path(state_root) if state_root else default_state_root()
        cache = Path(cache_root) if cache_root else default_cache_root()
        self.decrypt_assets = decrypt_assets
        self.mod_state_dir = state / "featured-mods" / DARK_MODE_ID
        self.state_path = self.mod_state_dir / "state.json"
        self.backup_dir = self.mod_state_dir / "backup"
        base_cache = cache / "featured-mods" / DARK_MODE_ID
        self.download_dir = base_cache / "downloads"
        self.extracted_dir = base_cache / "extracted"
        self.decoded_dir = base_cache / "decoded"
        self.client = client or GameBananaClient()

    @staticmethod
    def _default() -> dict[str, Any]:
        return {
            "version": 1,
            "first_offer_complete": False,
            "enabled": False,
            "status": "disabled",
            "metadata": {},
            "manifest": [],
        }

    def read_state(self) -> dict[str, Any]:
        state = _read_json(self.state_path, self._default())
        for key, value in self._default().items():
            state.setdefault(key, value)
        return state

    def write_state(self, state: dict[str, Any]) -> None:
        _write_json(self.state_path, state)

    def should_offer(self) -> bool:
        return not self.read_state()["first_offer_complete"]

    def mark_offer_complete(self) -> None:
        state = self.read_state()
        state["first_offer_complete"] = True
        self.write_state(state)

    def is_enabled(self) -> bool:
        state = self.read_state()
        return bool(state["enabled"]) and state["status"] in {"enabled", "conflicted"}

    def status_text(self) -> str:
        status = self.read_state()["status"]
        return {
            "enabled": "Enabled",
            "conflicted": "Partially enabled; restore conflicts remain",
        }.get(status, "Not installed")

    def prepare(self, progress: Progress | None = None) -> tuple[ModMetadata, Path, Path]:
        metadata = self.client.fetch_metadata()
        archive = self.client.download(metadata, self.download_dir, progress)
        if progress:
            progress("Checking and extracting the downloaded archive…")
        extract_archive(archive, self.extracted_dir)
        return metadata, archive, find_mod_root(self.extracted_dir)

    def _decode(self, mod_root: Path) -> tuple[list[Path], int, int]:
        assets = mod_root / "assets"
        if not assets.is_dir():
            raise FeaturedModError(f"Missing assets directory: {assets}")
        shutil.rmtree(self.decoded_dir, ignore_errors=True)
        self.decoded_dir.mkdir(parents=True, exist_ok=True)
        decoded, missing = self.decrypt_assets(
            str(assets), str(self.decoded_dir), use_hash=False, filter_path=None
        )
        files = sorted(path for path in self.decoded_dir.rglob("*") if path.is_file())
        if not files:
            raise FeaturedModError("No compatible game assets were produced.")
        return files, int(decoded), int(missing)

    def enable(
        self,
        metadata: ModMetadata,
        archive: Path,
        mod_root: Path,
        progress: Progress | None = None,
    ) -> InstallResult:
        if self.is_enabled():
            return InstallResult(0)
        if not self.dat_path.is_dir():
            raise FeaturedModError(f"Game data directory not found: {self.dat_path}")
        if progress:
            progress("Preparing dark-mode game assets…")
        files, decoded, missing = self._decode(mod_root)
        shutil.rmtree(self.backup_dir, ignore_errors=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        manifest: list[dict[str, Any]] = []
        applied: list[dict[str, Any]] = []
        try:
            for index, source in enumerate(files, 1):
                name = source.name
                if len(name) < 2:
                    raise FeaturedModError(f"Invalid decoded asset name: {name}")
                relative = Path(name[:2]) / name
                target, backup = self.dat_path / relative, self.backup_dir / relative
                had_original = target.is_file()
                if had_original:
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup)
                record = {"path": relative.as_posix(), "had_original": had_original, "installed_sha256": ""}
                applied.append(record)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                record["installed_sha256"] = _sha256(target)
                manifest.append(record)
                if progress:
                    progress(f"Installing dark mode asset {index} / {len(files)}")
        except Exception as exc:
            self._rollback(applied)
            raise FeaturedModError(f"Installation rolled back: {exc}") from exc
        finally:
            shutil.rmtree(self.decoded_dir, ignore_errors=True)
        state = self.read_state()
        state.update(
            {
                "first_offer_complete": True,
                "enabled": True,
                "status": "enabled",
                "enabled_at": _now(),
                "archive_path": str(archive),
                "archive_sha256": _sha256(archive),
                "metadata": metadata.__dict__,
                "manifest": manifest,
                "decoded_count": decoded,
                "missing_meta": missing,
            }
        )
        self.write_state(state)
        return InstallResult(len(manifest), max(0, missing))

    def _rollback(self, records: Iterable[dict[str, Any]]) -> None:
        for record in reversed(list(records)):
            relative = Path(record["path"])
            target, backup = self.dat_path / relative, self.backup_dir / relative
            if record["had_original"] and backup.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)
            else:
                target.unlink(missing_ok=True)

    def disable(self, progress: Progress | None = None) -> InstallResult:
        state = self.read_state()
        records = state.get("manifest")
        if not isinstance(records, list) or not records:
            state.update(enabled=False, status="disabled", manifest=[])
            self.write_state(state)
            return InstallResult(0)
        restored, conflicts, remaining = 0, [], []
        for index, record in enumerate(records, 1):
            relative = Path(str(record.get("path", "")))
            try:
                _safe_path(relative.as_posix())
            except FeaturedModError:
                conflicts.append(relative.as_posix())
                remaining.append(record)
                continue
            target, backup = self.dat_path / relative, self.backup_dir / relative
            expected = str(record.get("installed_sha256") or "")
            if target.is_file() and expected and _sha256(target) != expected:
                conflicts.append(relative.as_posix())
                remaining.append(record)
                continue
            if record.get("had_original"):
                if not backup.is_file():
                    conflicts.append(relative.as_posix())
                    remaining.append(record)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)
            else:
                target.unlink(missing_ok=True)
            restored += 1
            if progress:
                progress(f"Restoring original asset {index} / {len(records)}")
        state.update(
            enabled=bool(conflicts),
            status="conflicted" if conflicts else "disabled",
            disabled_at=_now(),
            manifest=remaining,
            restore_conflicts=conflicts,
        )
        if not conflicts:
            shutil.rmtree(self.backup_dir, ignore_errors=True)
        self.write_state(state)
        return InstallResult(restored, conflicts=tuple(conflicts))
