#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/umml"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
MAMBA_BIN="$APP_DIR/bin/micromamba"
MAMBA_ROOT="$APP_DIR/mamba-root"
ENV_DIR="$APP_DIR/env"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SCRIPT="$SCRIPT_DIR/UMML.py"
SOURCE_CORE="$SCRIPT_DIR/UMML_core.py"
SOURCE_PLATFORM="$SCRIPT_DIR/umml_platform.py"
SOURCE_AUTODETECT="$SCRIPT_DIR/umml_autodetect"
SOURCE_REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
SOURCE_DATA="$SCRIPT_DIR/UMML_data"
TARGET_SCRIPT="$APP_DIR/UMML.py"
TARGET_CORE="$APP_DIR/UMML_core.py"
TARGET_PLATFORM="$APP_DIR/umml_platform.py"
TARGET_AUTODETECT="$APP_DIR/umml_autodetect"
TARGET_REQUIREMENTS="$APP_DIR/requirements.txt"
TARGET_DATA="$APP_DIR/UMML_data"
LAUNCHER="$BIN_DIR/umml"
DOCTOR="$BIN_DIR/umml-doctor"
DESKTOP_FILE="$DESKTOP_DIR/umml.desktop"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/umml"
LOG_FILE="$STATE_DIR/umml.log"

fatal() {
    printf '\nERROR: %s\n' "$*" >&2
    exit 1
}

fetch_try() {
    local url="$1" out="$2"
    rm -f "$out"
    if command -v curl >/dev/null 2>&1; then
        curl --fail --location --retry 2 --connect-timeout 20 --silent --show-error "$url" -o "$out"
    elif command -v wget >/dev/null 2>&1; then
        wget --tries=3 --timeout=20 --quiet --show-progress -O "$out" "$url"
    else
        return 127
    fi
}

command -v tar >/dev/null 2>&1 || fatal "tar is required."
[[ -f "$SOURCE_SCRIPT" ]] || fatal "UMML.py must be beside this installer."
[[ -f "$SOURCE_CORE" ]] || fatal "UMML_core.py must be beside this installer."
[[ -f "$SOURCE_PLATFORM" ]] || fatal "umml_platform.py must be beside this installer."
[[ -f "$SOURCE_AUTODETECT/__init__.py" ]] || fatal "umml_autodetect package is missing."
[[ -f "$SOURCE_REQUIREMENTS" ]] || fatal "requirements.txt must be beside this installer."
[[ -f "$SOURCE_DATA/dropdown.json" ]] || fatal "UMML_data/dropdown.json is missing."
command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 || \
    fatal "Install curl or wget first."

case "$(uname -m)" in
    x86_64|amd64)
        MAMBA_PLATFORM="linux-64"
        MAMBA_ASSET="micromamba-linux-64"
        ;;
    aarch64|arm64)
        MAMBA_PLATFORM="linux-aarch64"
        MAMBA_ASSET="micromamba-linux-aarch64"
        ;;
    *) fatal "Unsupported CPU architecture: $(uname -m)" ;;
esac

mkdir -p "$APP_DIR/bin" "$BIN_DIR" "$DESKTOP_DIR" "$STATE_DIR"

if [[ ! -x "$MAMBA_BIN" ]]; then
    if command -v micromamba >/dev/null 2>&1; then
        printf 'Using the micromamba already installed on this system...\n'
        install -m 0755 "$(command -v micromamba)" "$MAMBA_BIN"
    else
        printf 'Downloading micromamba for the isolated Python/Tk environment...\n'
        tmpdir="$(mktemp -d)"
        trap 'rm -rf "$tmpdir"' EXIT
        archive="$tmpdir/micromamba.tar.bz2"
        binary="$tmpdir/micromamba"
        if fetch_try "https://micro.mamba.pm/api/micromamba/${MAMBA_PLATFORM}/latest" "$archive" \
            && tar -tjf "$archive" bin/micromamba >/dev/null 2>&1; then
            tar -xjf "$archive" -C "$tmpdir" bin/micromamba
            install -m 0755 "$tmpdir/bin/micromamba" "$MAMBA_BIN"
        elif fetch_try "https://github.com/mamba-org/micromamba-releases/releases/latest/download/${MAMBA_ASSET}" "$binary"; then
            install -m 0755 "$binary" "$MAMBA_BIN"
        else
            fatal "Could not download micromamba from either official source. Check DNS/internet access and run install.sh again."
        fi
        rm -rf "$tmpdir"
        trap - EXIT
    fi
fi

"$MAMBA_BIN" --version >/dev/null 2>&1 || fatal "The micromamba executable is invalid. Remove $MAMBA_BIN and rerun the installer."
export MAMBA_ROOT_PREFIX="$MAMBA_ROOT"

if [[ ! -x "$ENV_DIR/bin/python" ]]; then
    printf 'Creating private Python 3.11 + Tk environment...\n'
    "$MAMBA_BIN" create --yes --prefix "$ENV_DIR" --channel conda-forge python=3.11 tk pip
else
    printf 'Reusing the existing private Python environment.\n'
fi

printf 'Installing the tested UMML Python requirements...\n'
"$ENV_DIR/bin/python" -m pip install --disable-pip-version-check --upgrade pip setuptools wheel
"$ENV_DIR/bin/python" -m pip install --disable-pip-version-check --upgrade -r "$SOURCE_REQUIREMENTS"

install -m 0644 "$SOURCE_SCRIPT" "$TARGET_SCRIPT"
install -m 0644 "$SOURCE_CORE" "$TARGET_CORE"
install -m 0644 "$SOURCE_PLATFORM" "$TARGET_PLATFORM"
rm -rf "$TARGET_AUTODETECT"
mkdir -p "$TARGET_AUTODETECT"
find "$SOURCE_AUTODETECT" -maxdepth 1 -type f -name '*.py' -exec install -m 0644 {} "$TARGET_AUTODETECT/" \;
rm -f \
    "$APP_DIR/sitecustomize.py" \
    "$APP_DIR/umml_detection_hotfix.py" \
    "$APP_DIR/umml_manual_location_fix.py"
install -m 0644 "$SOURCE_REQUIREMENTS" "$TARGET_REQUIREMENTS"
rm -rf "$TARGET_DATA"
mkdir -p "$TARGET_DATA"
install -m 0644 "$SOURCE_DATA/dropdown.json" "$TARGET_DATA/dropdown.json"

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
export MAMBA_ROOT_PREFIX="$MAMBA_ROOT"
cd "$APP_DIR"
if [[ -t 1 ]] || [[ " \$* " == *" --doctor "* ]]; then
    exec "$ENV_DIR/bin/python" "$TARGET_SCRIPT" "\$@"
else
    mkdir -p "$STATE_DIR"
    {
        printf '\\n===== UMML launch %s =====\\n' "\$(date --iso-8601=seconds 2>/dev/null || date)"
        exec "$ENV_DIR/bin/python" "$TARGET_SCRIPT" "\$@"
    } >>"$LOG_FILE" 2>&1
fi
EOF
chmod 0755 "$LAUNCHER"

cat > "$DOCTOR" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
exec "$LAUNCHER" --doctor
EOF
chmod 0755 "$DOCTOR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=UMML
Comment=Load, preview, back up, and restore Umamusume mods
Exec=$LAUNCHER
Path=$APP_DIR
Terminal=false
Icon=applications-games
Categories=Game;Utility;
StartupNotify=true
EOF
chmod 0644 "$DESKTOP_FILE"

printf 'Checking imports and source code...\n'
"$ENV_DIR/bin/python" - <<'PY'
import tkinter
import UnityPy
import vdf
import apsw
import yaml
print("Tk:", tkinter.TkVersion)
print("UnityPy:", getattr(UnityPy, "__version__", "installed"))
print("vdf:", getattr(vdf, "__version__", "3.4"))
print("APSW SQLite3MC:", getattr(apsw, "mc_version", "installed"))
print("PyYAML:", getattr(yaml, "__version__", "installed"))
PY
"$ENV_DIR/bin/python" -m py_compile \
    "$TARGET_SCRIPT" "$TARGET_CORE" "$TARGET_PLATFORM" \
    "$TARGET_AUTODETECT"/*.py

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

printf '\nInstallation complete. No reboot is required.\n\n'
printf '1. Check the real game paths:\n   %s\n\n' "$DOCTOR"
printf '2. Start UMML:\n   %s\n\n' "$LAUNCHER"
printf 'Desktop-launch log:\n   %s\n\n' "$LOG_FILE"
printf 'You can also open “UMML” from the application menu.\n'
