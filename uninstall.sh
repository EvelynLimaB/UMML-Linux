#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/umml"
DESKTOP_FILE="${XDG_DATA_HOME:-$HOME/.local/share}/applications/umml.desktop"
rm -rf "$APP_DIR"
rm -f "$HOME/.local/bin/umml" "$HOME/.local/bin/umml-doctor" "$DESKTOP_FILE"
printf 'UMML Linux installation removed. Game files and UMML backups were not touched.\n'
