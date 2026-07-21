#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLE="${1:-$ROOT/build/frozen/umml}"
OUT_DIR="${2:-$ROOT/dist}"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
DESKTOP_ID="io.github.evelynlimab.umml"
ARCH_RAW="$(uname -m)"

case "$ARCH_RAW" in
  x86_64|amd64) APPIMAGE_ARCH="x86_64" ;;
  *) echo "AppImage packaging currently supports x86_64 only (got $ARCH_RAW)" >&2; exit 1 ;;
esac

[[ -x "$BUNDLE/umml" ]] || { echo "Frozen bundle not found: $BUNDLE" >&2; exit 1; }
APPDIR="$ROOT/build/appimage/UMML.AppDir"
PAYLOAD="$APPDIR/usr/lib/umml"
rm -rf "$APPDIR"
mkdir -p \
  "$PAYLOAD" \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps" \
  "$APPDIR/usr/share/metainfo"
cp -a "$BUNDLE/." "$PAYLOAD/"

cat > "$APPDIR/usr/bin/umml" <<'LAUNCHER'
#!/usr/bin/env bash
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE/lib/umml"
exec "$HERE/lib/umml/umml" "$@"
LAUNCHER
cat > "$APPDIR/usr/bin/umml-doctor" <<'DOCTOR'
#!/usr/bin/env bash
set -Eeuo pipefail
exec "$(dirname -- "$0")/umml" --doctor
DOCTOR
chmod 0755 "$APPDIR/usr/bin/umml" "$APPDIR/usr/bin/umml-doctor"

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/usr/bin/env bash
set -Eeuo pipefail
APPDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$APPDIR/usr/bin:${PATH:-}"
exec "$APPDIR/usr/bin/umml" "$@"
APPRUN
chmod 0755 "$APPDIR/AppRun"

install -m 0644 "$ROOT/packaging/linux/$DESKTOP_ID.desktop" \
  "$APPDIR/usr/share/applications/$DESKTOP_ID.desktop"
install -m 0644 "$ROOT/assets/umml.svg" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps/$DESKTOP_ID.svg"
install -m 0644 "$ROOT/packaging/linux/$DESKTOP_ID.metainfo.xml" \
  "$APPDIR/usr/share/metainfo/$DESKTOP_ID.metainfo.xml"
cp "$APPDIR/usr/share/applications/$DESKTOP_ID.desktop" "$APPDIR/$DESKTOP_ID.desktop"
ln -s "usr/share/icons/hicolor/scalable/apps/$DESKTOP_ID.svg" "$APPDIR/$DESKTOP_ID.svg"

TOOL="${APPIMAGETOOL:-$ROOT/build/tools/appimagetool-$APPIMAGE_ARCH.AppImage}"
if [[ ! -x "$TOOL" ]]; then
  mkdir -p "$(dirname -- "$TOOL")"
  URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$APPIMAGE_ARCH.AppImage"
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 3 --silent --show-error "$URL" -o "$TOOL"
  elif command -v wget >/dev/null 2>&1; then
    wget --tries=3 --timeout=30 -O "$TOOL" "$URL"
  else
    echo "curl or wget is required to download appimagetool" >&2
    exit 1
  fi
  chmod 0755 "$TOOL"
fi

mkdir -p "$OUT_DIR"
OUTPUT="$OUT_DIR/UMML-${VERSION}-${APPIMAGE_ARCH}.AppImage"
rm -f "$OUTPUT"
ARCH="$APPIMAGE_ARCH" APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" "$APPDIR" "$OUTPUT"
chmod 0755 "$OUTPUT"
[[ -s "$OUTPUT" ]] || { echo "AppImage was not created" >&2; exit 1; }
printf 'Built AppImage: %s\n' "$OUTPUT"
