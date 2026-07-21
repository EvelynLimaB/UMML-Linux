from __future__ import annotations

import shutil
import sys
import types
from pathlib import Path

from .models import ModRecord
from .store import ManagerStore, StoreError, hash_file


class _NullWidget:
    def __setitem__(self, key, value):
        return None

    def config(self, **kwargs):
        return None


class _NullRoot:
    def update_idletasks(self):
        return None


class LegacyAssetAdapter:
    """Reuse UMML's proven metadata lookup/encryption routine without its GUI."""

    def __init__(self, store: ManagerStore, meta_path: str | Path):
        self.store = store
        self.meta_path = Path(meta_path)

    def prepare(self, record: ModRecord) -> ModRecord:
        source = Path(record.source_path)
        assets = source / "assets"
        if not assets.is_dir():
            raise StoreError(f"Missing assets folder: {assets}")
        if not self.meta_path.is_file():
            raise StoreError(f"Metadata database not found: {self.meta_path}")
        output = self.store.paths.prepared / record.id / record.version
        shutil.rmtree(output, ignore_errors=True)
        output.mkdir(parents=True, exist_ok=True)
        decoder = self._decoder()
        _decoded, missing = decoder.decrypt_assets_internal(
            str(assets), str(output), use_hash=False, filter_path=None
        )
        files: dict[str, str] = {}
        for path in sorted(item for item in output.rglob("*") if item.is_file()):
            name = path.name
            if len(name) < 2:
                continue
            destination = output / name[:2] / name
            if path != destination:
                destination.parent.mkdir(parents=True, exist_ok=True)
                path.replace(destination)
            files[(Path(name[:2]) / name).as_posix()] = hash_file(destination)
        if not files:
            raise StoreError(f"No compatible assets produced; {missing} entries were absent from metadata")
        record.prepared_path = str(output)
        record.files = files
        self.store.save_mod(record)
        return record

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
