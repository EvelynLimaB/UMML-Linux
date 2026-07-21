#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m py_compile \
  UMML.py UMML_core.py umml_platform.py umml_packaged.py \
  umml_autodetect/*.py

python3 -m unittest discover -s tests -v

bash -n \
  install.sh uninstall.sh \
  scripts/build_release.sh \
  scripts/build_frozen.sh \
  scripts/build_deb.sh \
  scripts/build_appimage.sh \
  scripts/check_legacy.sh

scripts/build_release.sh
