from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class InstallationError(RuntimeError):
    """Raised when UMML cannot find or prepare a compatible installation."""


@dataclass(frozen=True)
class ManagerInstallation:
    key: str
    label: str
    region: str
    game_dir: Path
    dat_path: Path
    meta_source: Path
    meta_path: Path


Decryptor = Callable[[Path, Path, str], Path]


def detect_preferred_installation(
    preferred_region: str = "",
    *,
    decryptor: Decryptor | None = None,
) -> ManagerInstallation:
    """Detect the best installation and prepare its readable metadata cache."""

    from umml_platform import detect_installations

    detected = [item for item in detect_installations() if item.detected]
    if not detected:
        raise InstallationError(
            "No complete Umamusume installation was detected. Launch the game once, "
            "let its data finish downloading, then run diagnostics."
        )

    preferred = _normalize_region(preferred_region)
    selected = next(
        (item for item in detected if _normalize_region(item.region) == preferred),
        detected[0],
    )
    if selected.game_dir is None or selected.dat_path is None or selected.meta_path is None:
        raise InstallationError(f"{selected.label} was detected without all required paths.")

    game_dir = Path(selected.game_dir).expanduser().resolve()
    dat_path = Path(selected.dat_path).expanduser().resolve()
    meta_source = Path(selected.meta_path).expanduser().resolve()
    prepare = decryptor or prepare_metadata_database
    meta_path = Path(prepare(dat_path, meta_source, selected.region)).expanduser().resolve()

    if not dat_path.is_dir():
        raise InstallationError(f"Detected asset directory does not exist: {dat_path}")
    if not game_dir.is_dir():
        raise InstallationError(f"Detected game directory does not exist: {game_dir}")
    if not meta_path.is_file():
        raise InstallationError(f"Prepared metadata database does not exist: {meta_path}")

    return ManagerInstallation(
        key=selected.key,
        label=selected.label,
        region=_normalize_region(selected.region),
        game_dir=game_dir,
        dat_path=dat_path,
        meta_source=meta_source,
        meta_path=meta_path,
    )


def prepare_metadata_database(dat_path: Path, meta_path: Path, region: str) -> Path:
    """Return a readable metadata DB, creating the cached decrypted copy if needed."""

    if sys.platform != "win32" and "winreg" not in sys.modules:
        stub = types.ModuleType("winreg")
        stub.HKEY_CURRENT_USER = object()
        stub.HKEY_LOCAL_MACHINE = object()
        sys.modules["winreg"] = stub

    try:
        import UMML_core as core
    except Exception as exc:
        raise InstallationError(f"Could not load UMML metadata support: {exc}") from exc

    try:
        prepared = core.load_or_decrypt_meta_simple(
            str(dat_path),
            str(meta_path),
            _legacy_region(region),
        )
    except Exception as exc:
        raise InstallationError(f"Could not prepare the metadata database: {exc}") from exc
    return Path(prepared)


def _normalize_region(value: str) -> str:
    text = str(value or "").strip().casefold()
    aliases = {
        "global": "global",
        "steam global": "global",
        "en": "global",
        "japan": "japan",
        "japanese": "japan",
        "jp": "japan",
        "taiwan": "taiwan",
        "tw": "taiwan",
        "korea": "korea",
        "kr": "korea",
    }
    return aliases.get(text, text or "global")


def _legacy_region(value: str) -> str:
    normalized = _normalize_region(value)
    return {
        "global": "Global",
        "japan": "Japan",
        "taiwan": "Taiwan",
        "korea": "Korea",
    }.get(normalized, str(value))
