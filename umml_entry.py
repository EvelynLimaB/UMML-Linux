#!/usr/bin/env python3
"""UMML launcher that installs optional UI and safety extensions before startup."""

from __future__ import annotations

import UMML as application
from umml_featured_ui import install_featured_ui
from umml_legacy_safety import install_legacy_safety

install_legacy_safety(application.ModLoaderGUI)
install_featured_ui(application.ModLoaderGUI)


def set_display_version(version: str) -> None:
    application.MODLOADER_VERSION = version


def main() -> int:
    return application.main()


if __name__ == "__main__":
    raise SystemExit(main())
