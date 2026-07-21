#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m py_compile \
  umml_manager/*.py \
  umml_manager/providers/*.py \
  umml_manager_packaged.py \
  tests/test_manager.py

python3 -m unittest discover -s tests -p 'test_manager.py' -v

bash -n \
  install-manager.sh \
  uninstall-manager.sh \
  scripts/build_manager_frozen.sh \
  scripts/build_manager_deb.sh \
  scripts/check_manager.sh

if command -v desktop-file-validate >/dev/null 2>&1; then
  desktop-file-validate \
    packaging/linux/io.github.evelynlimab.ummlmanager.desktop
else
  printf 'Skipping desktop-file validation: desktop-file-validate not installed.\n' >&2
fi

if command -v appstream-util >/dev/null 2>&1; then
  appstream-util validate-relax \
    packaging/linux/io.github.evelynlimab.ummlmanager.metainfo.xml
else
  printf 'Skipping AppStream validation: appstream-util not installed.\n' >&2
fi
