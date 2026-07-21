#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/umml-manager"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
DESKTOP_ID="io.github.evelynlimab.ummlmanager"

rm -f "$BIN_DIR/umml-manager" "$BIN_DIR/umml-manager-cli"
rm -f "$DESKTOP_DIR/$DESKTOP_ID.desktop"
rm -f "$ICON_ROOT/scalable/apps/$DESKTOP_ID.svg"
rm -rf "$APP_DIR"

command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -q -t -f "$ICON_ROOT" >/dev/null 2>&1 || true

printf 'UMML Manager application files removed.\n'
printf 'Game backups, deployed game files, and XDG state/cache data were not modified.\n'
