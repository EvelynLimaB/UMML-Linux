from __future__ import annotations

import os
import shutil
import sys
import tempfile
import types
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from .locking import FileLock, LockError
from .models import PACKAGE_UMML_ASSETS, ModRecord
from .safety import SafetyError, atomic_copy_file, hash_file, validate_regular_tree
from .store import ManagerStore, StoreError


class _NullWidget:
    def __setitem__(self, key, value):
        return None

    def config(self, **kwargs):
        return None


class _NullRoot:
    def update_idletasks(self):
        return None


class LegacyAssetAdapter:
    """Reuse UMML's metadata lookup/encryption routine without its GUI."""

    def __init__(self, store: ManagerStore, meta_path: str | Path):
        self.store = store
        self.meta_path = Path(meta_path).expanduser()

    def prepare(self, record: ModRecord) -> ModRecord:
        if record.package_type != PACKAGE_UMML_ASSETS:
            raise StoreError(
                f"{record.name} is a {record.package_type} package and cannot be prepared "
                "by the legacy asset decoder."
            )
        source = Path(record.source_path)
        assets = source / "assets"
        if not assets.is_dir():
            raise StoreError(f"Missing assets folder: {assets}")
        if not self.meta_path.is_file():
            raise StoreError(f"Metadata database not found: {self.meta_path}")
        try:
            validate_regular_tree(assets)
        except SafetyError as exc:
            raise StoreError(str(exc)) from exc

        output = self.store.prepared_destination(record)
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with FileLock(
                self.store.paths.locks / f"prepare-{record.id}.lock",
                purpose=f"preparing {record.id}",
            ):
                return self._prepare_locked(record, assets, output)
        except LockError as exc:
            raise StoreError(str(exc)) from exc

    def _prepare_locked(self, record: ModRecord, assets: Path, output: Path) -> ModRecord:
        stage_root = Path(
            tempfile.mkdtemp(prefix=f".{output.name}-prepare-", dir=output.parent)
        )
        decoded = stage_root / "decoded"
        normalized = stage_root / "normalized"
        decoded.mkdir()
        normalized.mkdir()
        backup = output.with_name(
            f".{output.name}.previous-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        )
        moved_old = False
        moved_new = False
        try:
            decoder = self._decoder()
            _decoded_count, missing = decoder.decrypt_assets_internal(
                str(assets),
                str(decoded),
                use_hash=False,
                filter_path=None,
            )
            try:
                validate_regular_tree(decoded)
            except SafetyError as exc:
                raise StoreError(f"Prepared output was unsafe: {exc}") from exc

            files: dict[str, str] = {}
            for path in sorted(item for item in decoded.rglob("*") if item.is_file()):
                name = path.name
                if len(name) < 2:
                    continue
                relative = (Path(name[:2]) / name).as_posix()
                destination = normalized / name[:2] / name
                if relative in files:
                    raise StoreError(
                        f"Preparation produced duplicate target hash {name}; existing cache was preserved."
                    )
                atomic_copy_file(path, destination)
                files[relative] = hash_file(destination)
            if not files:
                raise StoreError(
                    f"No compatible assets produced; {missing} entries were absent from metadata. "
                    "The previous prepared cache was preserved."
                )

            if output.exists():
                os.replace(output, backup)
                moved_old = True
            os.replace(normalized, output)
            moved_new = True
            updated = replace(
                record,
                prepared_path=str(output),
                files=files,
                prepared_against=hash_file(self.meta_path),
                prepared_at=datetime.now(timezone.utc).isoformat(),
            )
            try:
                self.store.save_mod(updated)
            except Exception:
                if moved_new and output.exists():
                    shutil.rmtree(output, ignore_errors=True)
                if moved_old and backup.exists():
                    os.replace(backup, output)
                raise
            shutil.rmtree(backup, ignore_errors=True)
            return updated
        finally:
            shutil.rmtree(stage_root, ignore_errors=True)
            if backup.exists() and not output.exists():
                os.replace(backup, output)

    def _decoder(self):
        if sys.platform != "win32" and "winreg" not in sys.modules:
            stub = types.ModuleType("winreg")
            stub.HKEY_CURRENT_USER = object()
            stub.HKEY_LOCAL_MACHINE = object()
            sys.modules["winreg"] = stub
        try:
            import UMML_core as core
        except Exception as exc:
            raise StoreError(f"Could not load UMML's asset adapter: {exc}") from exc

        meta_path = str(self.meta_path)

        class Decoder:
            progress_bar = _NullWidget()
            progress_label = _NullWidget()
            root = _NullRoot()

            def __init__(self):
                self.meta_path = meta_path

            @staticmethod
            def scan_full_path(root):
                root_path = Path(root)
                for item in root_path.rglob("*"):
                    if item.is_file():
                        yield item.relative_to(root_path).as_posix()

        Decoder.decrypt_assets_internal = core.ModLoaderGUI.decrypt_assets_internal
        return Decoder()
