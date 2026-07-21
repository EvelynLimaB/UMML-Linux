# Linux and Steam Proton guide

## Linux Mint, Ubuntu, or Debian

```bash
sudo apt install ./umml-linux_1.5.0-linux.4_amd64.deb
umml-doctor
umml
```

The DEB is self-contained and upgrades older UMML Linux packages in place.
Remove it with `sudo apt remove umml-linux`. Removing UMML does not remove game
files or `dat.backup`.

## Portable AppImage

```bash
chmod +x UMML-1.5.0-linux.4-x86_64.AppImage
./UMML-1.5.0-linux.4-x86_64.AppImage
```

Without FUSE 2:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./UMML-1.5.0-linux.4-x86_64.AppImage
```

## Source installer

```bash
unzip UMML-1.5.0-linux.4.zip
cd UMML-1.5.0-linux.4
chmod +x install.sh uninstall.sh
./install.sh
```

The source installer creates a private Python/Tk environment inside the current
user account. It does not modify system Python.

## First launch

1. Start Umamusume Pretty Derby Global and allow its data download to finish.
2. Close the game before loading or restoring assets.
3. Run `umml-doctor`.
4. Start `umml`.

## Steam layouts detected

- Mint/Ubuntu/Debian Steam: `~/.steam/debian-installation`
- Native Steam: `~/.local/share/Steam`, `~/.steam/steam`, `~/.steam/root`
- Flatpak Steam under `~/.var/app/com.valvesoftware.Steam/`
- Snap Steam under `~/snap/steam/common/`
- Secondary libraries from `libraryfolders.vdf`
- Running Steam and Proton process paths
- Proton prefixes under `steamapps/compatdata/<app-id>/pfx`

Steam Global uses app ID `3224770`.

## Manual selection in `.4`

The game directory and writable game data are not always the same folder.
Steam may expose the game through a symlink while Proton stores metadata under:

```text
steamapps/compatdata/3224770/pfx/drive_c/users/steamuser/
AppData/LocalLow/Cygames/umamusume
```

The manual chooser accepts:

- the game root containing `UmamusumePrettyDerby_Data`;
- `UmamusumePrettyDerby_Data`;
- `Persistent`;
- `LocalLow/Cygames/umamusume` containing `meta` and `dat`;
- the `dat` subfolder.

When UMML accepts the game root but cannot find its data automatically, it opens
a second chooser. Select `Persistent` or `LocalLow/Cygames/umamusume`—the parent
folder containing both `meta` and `dat`.

## Overrides

```bash
UMML_PLATFORM=steam-global \
UMML_STEAM_ROOT="/mnt/games/SteamLibrary" \
UMML_GAME_DIR="/mnt/games/SteamLibrary/steamapps/common/UmamusumePrettyDerby" \
UMML_PERSISTENT_DIR="/mnt/games/uma-data" \
umml
```

`UMML_PERSISTENT_DIR` must point to the parent containing `meta` and `dat`, not
to `dat` itself.

## Troubleshooting

### Automatic detection fails

Run:

```bash
umml-doctor
```

Then use the two-step manual selection described above. The first folder is the
game root; the optional second folder is the writable Persistent/LocalLow data.

### Game found; data missing

The game directory was detected, but `meta` and `dat` were not. Let the game
finish its data download or select the Proton LocalLow data folder manually.

### AppImage does not start

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./UMML-*.AppImage
```

### Logs

Terminal launches print errors directly. Source-installed desktop launches log
to:

```text
~/.local/state/umml/umml.log
```

## Updating

- DEB: install the newer package with `sudo apt install ./new-package.deb`
- AppImage: replace the old AppImage
- Source install: extract the new version and rerun `./install.sh`
