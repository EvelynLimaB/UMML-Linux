#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT/build/frozen}"
WORK_DIR="${PYINSTALLER_WORK_DIR:-$ROOT/build/pyinstaller-work}"
SPEC="$ROOT/packaging/pyinstaller/umml.spec"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"

[[ -n "$VERSION" ]] || { echo "VERSION is empty" >&2; exit 1; }
python3 -c 'import PyInstaller' >/dev/null 2>&1 || {
  echo "PyInstaller is missing. Install requirements-build.txt first." >&2
  exit 1
}

rm -rf "$OUT_DIR" "$WORK_DIR"
mkdir -p "$OUT_DIR" "$WORK_DIR"
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "$OUT_DIR" \
  --workpath "$WORK_DIR" \
  "$SPEC"

BUNDLE="$OUT_DIR/umml"
[[ -x "$BUNDLE/umml" ]] || { echo "Frozen UMML executable was not created" >&2; exit 1; }
ACTUAL_VERSION="$("$BUNDLE/umml" --version)"
[[ "$ACTUAL_VERSION" == "$VERSION" ]] || {
  echo "Frozen version mismatch: expected $VERSION, got $ACTUAL_VERSION" >&2
  exit 1
}

printf 'Built frozen runtime: %s\n' "$BUNDLE"
