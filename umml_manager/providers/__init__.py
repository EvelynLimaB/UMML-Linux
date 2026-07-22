from .base import ProviderDescriptor, ProviderRegistry
from .gamebanana import GameBananaClient, GameBananaFile, GameBananaMod

GameBananaClient.descriptor = ProviderDescriptor(  # type: ignore[attr-defined]
    id="gamebanana",
    name="GameBanana",
    supports_browse=True,
    supports_updates=True,
    supports_file_selection=True,
    regions=("global", "japan"),
)


def default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(GameBananaClient())
    return registry


__all__ = [
    "GameBananaClient",
    "GameBananaFile",
    "GameBananaMod",
    "ProviderDescriptor",
    "ProviderRegistry",
    "default_provider_registry",
]
