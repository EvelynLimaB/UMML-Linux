"""UMML Manager: deterministic profiles and transactional asset deployment."""

from .deployment import ApplyEngine, ApplyError
from .models import ModRecord, Profile
from .resolver import Resolution, resolve_profile
from .store import ManagerStore

__all__ = [
    "ApplyEngine",
    "ApplyError",
    "ManagerStore",
    "ModRecord",
    "Profile",
    "Resolution",
    "resolve_profile",
]
