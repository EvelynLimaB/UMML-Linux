from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ..models import ModRecord
from ..store import ManagerStore


@dataclass(frozen=True)
class ProviderDescriptor:
    id: str
    name: str
    supports_browse: bool
    supports_updates: bool
    supports_file_selection: bool
    regions: tuple[str, ...] = ()


@runtime_checkable
class ModProvider(Protocol):
    """Contract for remote mod catalogs.

    Providers own remote metadata, downloads, and provenance. They do not prepare
    assets, resolve profiles, or write into the game installation.
    """

    descriptor: ProviderDescriptor

    def import_mod(
        self,
        store: ManagerStore,
        value: str,
        *,
        file_id: int | None = None,
    ) -> ModRecord: ...

    def update_available(self, record: ModRecord) -> Any | None: ...


@runtime_checkable
class BrowsableProvider(ModProvider, Protocol):
    def browse(
        self,
        *,
        region: str,
        page: int = 1,
        per_page: int = 24,
        sort: str = "updated",
        query: str = "",
    ) -> Any: ...


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, ModProvider] = {}

    def register(self, provider: ModProvider) -> None:
        provider_id = provider.descriptor.id.strip().casefold()
        if not provider_id:
            raise ValueError("Provider ID cannot be empty")
        if provider_id in self._providers:
            raise ValueError(f"Provider already registered: {provider_id}")
        self._providers[provider_id] = provider

    def get(self, provider_id: str) -> ModProvider:
        key = provider_id.strip().casefold()
        try:
            return self._providers[key]
        except KeyError as exc:
            raise KeyError(f"Unknown provider: {provider_id}") from exc

    def descriptors(self) -> tuple[ProviderDescriptor, ...]:
        return tuple(
            provider.descriptor
            for _, provider in sorted(self._providers.items())
        )

    def values(self) -> tuple[ModProvider, ...]:
        return tuple(provider for _, provider in sorted(self._providers.items()))


def preserve_download_path(record: ModRecord) -> Path | None:
    """Return the recorded provider archive when its provenance still matches."""

    if not record.source.file_name or not record.source.sha256:
        return None
    source = Path(record.source_path)
    root = source.parents[2] if len(source.parents) >= 3 else None
    if root is None:
        return None
    candidate = root / "downloads" / str(record.source.submission_id or "local")
    matches = list(candidate.rglob(record.source.file_name)) if candidate.is_dir() else []
    return matches[0] if len(matches) == 1 else None
