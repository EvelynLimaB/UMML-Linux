# Linux and Steam Proton guide

## Install

### Mint, Ubuntu, Debian

```bash
sudo apt install ./umml-linux_1.5.0-linux.5_amd64.deb
umml-doctor
umml
```

### Portable AppImage

```bash
chmod +x UMML-1.5.0-linux.5-x86_64.AppImage
./UMML-1.5.0-linux.5-x86_64.AppImage
```

Without FUSE 2:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./UMML-1.5.0-linux.5-x86_64.AppImage
```

### Source installer

```bash
chmod +x install.sh
./install.sh
umml-doctor
umml
```

## What autodetection checks

- explicit `UMML_*` overrides;
- running Steam/Proton process environment;
- Mint/Debian, XDG, legacy, Flatpak, Snap, and system Steam roots;
- every configured secondary Steam library;
- old and new Valve KeyValues layouts;
- app manifests and case-insensitive marker scans;
- game-local `Persistent` data;
- every `compatdata/3224770/pfx` across every library;
- all Proton users under `drive_c/users`;
- symlink-preserving and canonical path variants;
- prefix recency through `pfx.lock`.

Game and data are deliberately not required to live on the same Steam library.
Detailed architecture and source references are in
[AUTODETECTION.md](AUTODETECTION.md).

## First launch

1. Run the game once and finish its initial download.
2. Close the game.
3. Run `umml-doctor`.
4. Confirm the report ends with `result: READY`.
5. Start `umml`.

The report lists evidence scores and exact selected paths. Keep the full output
when reporting a detection bug.

## Manual recovery

When only one half is discovered, select either:

- the game root containing `UmamusumePrettyDerby_Data` or the executable; or
- `Persistent`, `LocalLow/Cygames/umamusume`, or its `dat` subfolder.

UMML then asks for the missing half. The data directory must contain both
`meta` and `dat/`.

## Overrides

```bash
UMML_STEAM_ROOT="/mnt/games/SteamLibrary" \
UMML_GAME_DIR="/mnt/games/SteamLibrary/steamapps/common/UmamusumePrettyDerby" \
UMML_PERSISTENT_DIR="/mnt/prefix/AppData/LocalLow/Cygames/umamusume" \
umml
```

## Troubleshooting

```bash
umml --version
umml-doctor
tail -n 200 ~/.local/state/umml/umml.log
```

- **Game found, data missing:** let the game finish downloading or locate the
  Proton LocalLow folder containing `meta` and `dat`.
- **AppImage fails without FUSE:** use `APPIMAGE_EXTRACT_AND_RUN=1`.
- **External library unavailable:** verify it is mounted and writable with
  `findmnt` and `namei -l`.

Removing UMML never intentionally removes game data or `dat.backup`.
