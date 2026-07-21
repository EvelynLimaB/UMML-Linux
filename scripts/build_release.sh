#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
[[ -n "$VERSION" ]] || { echo "VERSION is empty" >&2; exit 1; }

OUT_DIR="${1:-$ROOT/dist}"
NAME="UMML-${VERSION}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$OUT_DIR" "$STAGE/$NAME/docs" "$STAGE/$NAME/UMML_data" "$STAGE/$NAME/assets"

install -m 0644 "$ROOT/UMML.py" "$STAGE/$NAME/UMML.py"
install -m 0644 "$ROOT/UMML_core.py" "$STAGE/$NAME/UMML_core.py"
install -m 0644 "$ROOT/umml_platform.py" "$STAGE/$NAME/umml_platform.py"
install -m 0644 "$ROOT/requirements.txt" "$STAGE/$NAME/requirements.txt"
install -m 0644 "$ROOT/VERSION" "$STAGE/$NAME/VERSION"
install -m 0644 "$ROOT/README.md" "$STAGE/$NAME/README.md"
install -m 0644 "$ROOT/CHANGELOG.md" "$STAGE/$NAME/CHANGELOG.md"
install -m 0644 "$ROOT/LICENSE" "$STAGE/$NAME/LICENSE"
install -m 0644 "$ROOT/docs/LINUX.md" "$STAGE/$NAME/docs/LINUX.md"
install -m 0644 "$ROOT/UMML_data/dropdown.json" "$STAGE/$NAME/UMML_data/dropdown.json"
install -m 0644 "$ROOT/assets/umml.svg" "$STAGE/$NAME/assets/umml.svg"
install -m 0755 "$ROOT/install.sh" "$STAGE/$NAME/install.sh"
install -m 0755 "$ROOT/uninstall.sh" "$STAGE/$NAME/uninstall.sh"

rm -f "$OUT_DIR/$NAME.zip" "$OUT_DIR/$NAME.tar.gz" "$OUT_DIR/SHA256SUMS"
(
  cd "$STAGE"
  python3 - "$NAME" "$OUT_DIR/$NAME.zip" <<'PY'
from pathlib import Path
import sys, zipfile
root = Path(sys.argv[1])
out = Path(sys.argv[2])
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            zf.write(path, path.as_posix())
PY
  tar -czf "$OUT_DIR/$NAME.tar.gz" "$NAME"
)
(
  cd "$OUT_DIR"
  sha256sum "$NAME.zip" "$NAME.tar.gz" > SHA256SUMS
)
printf 'Built release artifacts in %s\n' "$OUT_DIR"
