#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/umml-manager"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"
LEGACY_PYTHON="${XDG_DATA_HOME:-$HOME/.local/share}/umml/env/bin/python"
LAUNCHER="$BIN_DIR/umml-manager"
CLI_LAUNCHER="$BIN_DIR/umml-manager-cli"
DESKTOP_ID="io.github.evelynlimab.ummlmanager"
DESKTOP_FILE="$DESKTOP_DIR/$DESKTOP_ID.desktop"
ICON_FILE="$ICON_DIR/$DESKTOP_ID.svg"

fatal() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

[[ -d "$SOURCE_ROOT/umml_manager" ]] || fatal "umml_manager/ must be beside this installer."
[[ -f "$SOURCE_ROOT/UMML_core.py" ]] || fatal "UMML_core.py must be beside this installer."
[[ -f "$SOURCE_ROOT/MANAGER_VERSION" ]] || fatal "MANAGER_VERSION must be beside this installer."
[[ -f "$SOURCE_ROOT/assets/umml-manager.svg" ]] || fatal "Manager icon is missing."

if [[ -x "$LEGACY_PYTHON" ]]; then
    PYTHON="$LEGACY_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
else
    fatal "Python 3 is required. Install legacy UMML first or install Python 3 with Tk."
fi

"$PYTHON" - <<'PY' || fatal "The selected Python does not include Tkinter. Install legacy UMML first for its isolated environment."
import tkinter
print("Tk", tkinter.TkVersion)
PY

mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"
rm -rf "$APP_DIR/umml_manager"
cp -a "$SOURCE_ROOT/umml_manager" "$APP_DIR/umml_manager"
install -m 0644 "$SOURCE_ROOT/UMML_core.py" "$APP_DIR/UMML_core.py"
install -m 0644 "$SOURCE_ROOT/MANAGER_VERSION" "$APP_DIR/MANAGER_VERSION"
install -m 0644 "$SOURCE_ROOT/assets/umml-manager.svg" "$ICON_FILE"
[[ -f "$SOURCE_ROOT/requirements.txt" ]] && install -m 0644 "$SOURCE_ROOT/requirements.txt" "$APP_DIR/requirements.txt"
[[ -f "$SOURCE_ROOT/MANAGER_README.md" ]] && install -m 0644 "$SOURCE_ROOT/MANAGER_README.md" "$APP_DIR/MANAGER_README.md"
[[ -f "$SOURCE_ROOT/MANAGER_CHANGELOG.md" ]] && install -m 0644 "$SOURCE_ROOT/MANAGER_CHANGELOG.md" "$APP_DIR/MANAGER_CHANGELOG.md"

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
cd "$APP_DIR"
exec "$PYTHON" -m umml_manager.gui "\$@"
EOF
chmod 0755 "$LAUNCHER"

cat > "$CLI_LAUNCHER" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
cd "$APP_DIR"
exec "$PYTHON" -m umml_manager "\$@"
EOF
chmod 0755 "$CLI_LAUNCHER"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=UMML Manager
GenericName=UM:PD Mod Manager
Comment=Manage mod libraries, profiles, conflicts, and deployment
Exec=$LAUNCHER
Path=$APP_DIR
Terminal=false
Icon=$DESKTOP_ID
Categories=Game;Utility;
Keywords=UMML;Mod;Manager;Profiles;GameBanana;Steam;Proton;
StartupNotify=true
EOF
chmod 0644 "$DESKTOP_FILE"

"$PYTHON" -m py_compile "$APP_DIR"/umml_manager/*.py "$APP_DIR"/umml_manager/providers/*.py
"$CLI_LAUNCHER" --version >/dev/null

if ! "$PYTHON" - <<'PY'
import importlib
missing = []
for name in ("UnityPy", "yaml", "apsw", "vdf"):
    try:
        importlib.import_module(name)
    except Exception:
        missing.append(name)
if missing:
    raise SystemExit(", ".join(missing))
PY
then
    printf '\nWARNING: asset preparation dependencies are missing in %s.\n' "$PYTHON" >&2
    printf 'Install legacy UMML first, then rerun this installer to reuse its tested environment.\n' >&2
fi

command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -q -t -f "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" >/dev/null 2>&1 || true

printf '\nUMML Manager installed separately.\nGUI: %s\nCLI: %s\nVersion: %s\n' \
    "$LAUNCHER" "$CLI_LAUNCHER" "$("$CLI_LAUNCHER" --version)"
