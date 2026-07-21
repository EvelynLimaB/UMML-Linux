#!/usr/bin/env python3
"""Entry point used by the self-contained DEB and AppImage builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_root() -> Path:
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled).resolve()
    return Path(__file__).resolve().parent


ROOT = resource_root()
os.chdir(ROOT)

try:
    RELEASE_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
except OSError:
    RELEASE_VERSION = "1.5.0-hotfix"

if "--version" in sys.argv:
    print(RELEASE_VERSION)
    raise SystemExit(0)

import umml_entry as application  # noqa: E402

# Keep the upstream mod compatibility value inside UMML_core unchanged while
# presenting the fork's release version in the window title and About dialog.
application.set_display_version(RELEASE_VERSION)


if __name__ == "__main__":
    raise SystemExit(application.main())
