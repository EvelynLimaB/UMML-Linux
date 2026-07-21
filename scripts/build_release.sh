#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
[[ -n "$VERSION" ]] || { echo "VERSION is empty" >&2; exit 1; }

OUT_DIR="${1:-$ROOT/dist}"
NAME="UMML-${VERSION}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p \
  "$OUT_DIR" \
  "$STAGE/$NAME/docs" \
  "$STAGE/$NAME/UMML_data" \
  "$STAGE/$NAME/assets" \
  "$STAGE/$NAME/scripts" \
  "$STAGE/$NAME/packaging/pyinstaller" \
  "$STAGE/$NAME/packaging/linux"

for file in UMML.py UMML_core.py umml_platform.py umml_packaged.py umml_entry.py \
            umml_featured_mods.py umml_featured_ui.py umml_legacy_safety.py \
            requirements.txt requirements-build.txt VERSION README.md CHANGELOG.md RELEASE_NOTES.md \
            SECURITY.md CONTRIBUTING.md LICENSE THIRD_PARTY_NOTICES.md; do
  install -m 0644 "$ROOT/$file" "$STAGE/$NAME/$file"
done
install -m 0644 "$ROOT/docs/LINUX.md" "$STAGE/$NAME/docs/LINUX.md"
install -m 0644 "$ROOT/docs/AUTODETECTION.md" "$STAGE/$NAME/docs/AUTODETECTION.md"
mkdir -p "$STAGE/$NAME/umml_autodetect"
find "$ROOT/umml_autodetect" -maxdepth 1 -type f -name '*.py' -exec install -m 0644 {} "$STAGE/$NAME/umml_autodetect/" \;
install -m 0644 "$ROOT/UMML_data/dropdown.json" "$STAGE/$NAME/UMML_data/dropdown.json"
install -m 0644 "$ROOT/assets/umml.svg" "$STAGE/$NAME/assets/umml.svg"
install -m 0755 "$ROOT/install.sh" "$STAGE/$NAME/install.sh"
install -m 0755 "$ROOT/uninstall.sh" "$STAGE/$NAME/uninstall.sh"
for script in build_release.sh build_frozen.sh build_deb.sh build_appimage.sh; do
  install -m 0755 "$ROOT/scripts/$script" "$STAGE/$NAME/scripts/$script"
done
install -m 0644 "$ROOT/packaging/pyinstaller/umml.spec" \
  "$STAGE/$NAME/packaging/pyinstaller/umml.spec"
install -m 0644 "$ROOT/packaging/linux/io.github.evelynlimab.umml.desktop" \
  "$STAGE/$NAME/packaging/linux/io.github.evelynlimab.umml.desktop"
install -m 0644 "$ROOT/packaging/linux/io.github.evelynlimab.umml.metainfo.xml" \
  "$STAGE/$NAME/packaging/linux/io.github.evelynlimab.umml.metainfo.xml"

rm -f "$OUT_DIR/$NAME.zip" "$OUT_DIR/$NAME.tar.gz" "$OUT_DIR/SHA256SUMS"
(
  cd "$STAGE"
  python3 - "$NAME" "$OUT_DIR/$NAME.zip" <<'PY'
from pathlib import Path
import sys
import zipfile

root = Path(sys.argv[1])
out = Path(sys.argv[2])
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            archive.write(path, path.as_posix())
PY
  tar -czf "$OUT_DIR/$NAME.tar.gz" "$NAME"
)
(
  cd "$OUT_DIR"
  sha256sum "$NAME.zip" "$NAME.tar.gz" > SHA256SUMS
)
printf 'Built source release artifacts in %s\n' "$OUT_DIR"
