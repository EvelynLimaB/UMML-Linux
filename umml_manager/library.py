from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from . import store as _store
from .locking import FileLock, LockError
from .models import ModRecord, SourceSpec


class UnrecognizedModError(_store.StoreError):
    """Raised when a package contains no supported UMML or Hachimi root."""


_BaseManagerStore = getattr(
    _store,
    "_UMML_BASE_MANAGER_STORE",
    _store.ManagerStore,
)
_store._UMML_BASE_MANAGER_STORE = _BaseManagerStore  # type: ignore[attr-defined]

_base_find_mod_root = getattr(
    _store,
    "_UMML_BASE_FIND_MOD_ROOT",
    _store.find_mod_root,
)
_store._UMML_BASE_FIND_MOD_ROOT = _base_find_mod_root  # type: ignore[attr-defined]

_IMPORT_MUTEX = threading.RLock()


def find_mod_root(extracted: Path) -> Path:
    try:
        return _base_find_mod_root(extracted)
    except _store.StoreError as exc:
        if str(exc).startswith("No recognizable UMML/Hachimi mod folder"):
            raise UnrecognizedModError(str(exc)) from exc
        raise


class ManagerStore(_BaseManagerStore):
    """Manager store with whole-import identity allocation serialization.

    Threads in one manager process wait on the local mutex. A separate manager
    process still receives the normal fail-fast advisory-lock error instead of
    waiting indefinitely behind an invisible application.
    """

    def import_folder(
        self,
        folder: str | Path,
        *,
        mod_id: str | None = None,
        source: SourceSpec | None = None,
        metadata_overrides: dict[str, Any] | None = None,
    ) -> ModRecord:
        with _IMPORT_MUTEX:
            try:
                with FileLock(
                    self.paths.locks / "imports.lock",
                    purpose="allocating and importing an immutable mod version",
                ):
                    return super().import_folder(
                        folder,
                        mod_id=mod_id,
                        source=source,
                        metadata_overrides=metadata_overrides,
                    )
            except LockError as exc:
                raise _store.StoreError(str(exc)) from exc


# Compatibility bridge for modules that historically imported from store.py.
# Package initialization loads this boundary before GUI/CLI/provider modules.
_store.find_mod_root = find_mod_root
_store.ManagerStore = ManagerStore

StoreError = _store.StoreError
default_root = _store.default_root

__all__ = [
    "ManagerStore",
    "StoreError",
    "UnrecognizedModError",
    "default_root",
    "find_mod_root",
]
