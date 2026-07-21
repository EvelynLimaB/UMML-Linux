# Linux and Steam Proton guide

## Choose an installation format

### Linux Mint, Ubuntu, or Debian

Install the self-contained DEB from the latest release:

```bash
sudo apt install ./umml-linux_1.5.0-linux.3_amd64.deb
umml-doctor
umml
```

The package installs UMML under `/usr/lib/umml`, command launchers under
`/usr/bin`, and its desktop entry/icon under `/usr/share`. Python, Tk, and the
Python dependencies are bundled inside the package.

Remove it with:

```bash
sudo apt remove umml-linux
```

Removing the package does not touch game files, `dat.backup`, or metadata caches.

### Portable AppImage

```bash
chmod +x UMML-1.5.0-linux.3-x86_64.AppImage
./UMML-1.5.0-linux.3-x86_64.AppImage
```

The AppImage does not install files system-wide. On a distribution without FUSE
2, run it using AppImage's extraction fallback:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./UMML-1.5.0-linux.3-x86_64.AppImage
```

Desktop-menu integration is handled by tools such as AppImageLauncher when
available; UMML itself does not silently modify the system from an AppImage.

### Source/user-local installer

`install.sh` remains the fallback for unsupported binary-package architectures
and unusual environments. It installs UMML entirely inside the current user
account:

- application files: `${XDG_DATA_HOME:-~/.local/share}/umml`
- launchers: `~/.local/bin/umml` and `~/.local/bin/umml-doctor`
- desktop entry: `${XDG_DATA_HOME:-~/.local/share}/applications/umml.desktop`
- desktop-launch log: `${XDG_STATE_HOME:-~/.local/state}/umml/umml.log`

It downloads Micromamba from an official source and creates an isolated Python
3.11 environment containing Tk and the pinned Python dependencies. This avoids
`rpm-ostree`, system Python modification, and reboot requirements on Bazzite,
Fedora Atomic, and similar systems.

```bash
unzip UMML-1.5.0-linux.3.zip
cd UMML-1.5.0-linux.3
chmod +x install.sh uninstall.sh
./install.sh
```

Ensure `~/.local/bin` is in `PATH`. Logging out and back in may be necessary on
unusual desktop configurations, but UMML itself does not require a reboot.

## First launch

1. Start Umamusume Pretty Derby Global through Steam.
2. Let the game finish its initial data download.
3. Close the game before using UMML to modify or restore assets.
4. Run:

   ```bash
   umml-doctor
   ```

5. Confirm that Steam Global is detected and the report ends in `RESULT: READY`.
6. Run `umml` or select UMML from the desktop application menu.
7. If automatic discovery still fails, accept the manual-location prompt and
   select the folder containing `UmamusumePrettyDerby_Data`.

## Steam layouts detected automatically

- Mint/Ubuntu/Debian native Steam: `~/.steam/debian-installation`
- native Steam: `~/.local/share/Steam`
- legacy native Steam: `~/.steam/steam` and `~/.steam/root`
- Flatpak Steam data and legacy paths under `~/.var/app/com.valvesoftware.Steam/`
- Snap Steam paths under `~/snap/steam/common/`
- every secondary library listed in `libraryfolders.vdf`
- Steam roots and game paths inferred from running Steam/Proton processes
- Proton prefixes under `steamapps/compatdata/<app-id>/pfx`

For Steam Global, UMML checks the current
`UmamusumePrettyDerby_Data/Persistent` location first, then the older Proton
`AppData/LocalLow/Cygames/umamusume` location.

## Manual path overrides

```bash
UMML_PLATFORM=steam-global \
UMML_STEAM_ROOT="/mnt/games/SteamLibrary" \
UMML_GAME_DIR="/mnt/games/SteamLibrary/steamapps/common/Umamusume Pretty Derby" \
UMML_PERSISTENT_DIR="/mnt/games/uma-data" \
umml
```

The persistent directory must contain:

```text
meta
dat/
master/        # normally appears after game data has downloaded
```

## Flatpak Steam permissions

UMML itself is not installed as a Flatpak. It reads the Steam Flatpak's files
from the current user's home directory. Secondary libraries mounted outside the
home directory must be readable and writable by the current user.

Check access with:

```bash
namei -l /path/to/SteamLibrary
findmnt /path/to/SteamLibrary
```

A library mounted read-only cannot be used for mod loading or restoration.

## Logs and troubleshooting

Terminal launches print errors directly. The source installer's desktop launcher
appends output to:

```text
~/.local/state/umml/umml.log
```

Useful commands:

```bash
umml --version
umml-doctor
tail -n 200 ~/.local/state/umml/umml.log
```

### No Steam root detected

Release `1.5.0-linux.3` adds Mint's `~/.steam/debian-installation` path, runtime
Steam/Proton process discovery, and a built-in manifest parser. When those still
cannot identify the install, use the manual folder prompt or set
`UMML_STEAM_ROOT` to the directory containing `steamapps/`.

### Game found but metadata/data missing

Launch the game once and wait for its data download to finish. If the files are
in a nonstandard location, set `UMML_PERSISTENT_DIR` to their parent directory.

### Blank or apparently frozen window

This port creates the primary Tk root only once, parents the platform chooser to
it, and renders startup progress before scanning/decrypting metadata. Launch it
from a terminal to capture errors directly.

### AppImage does not start

Try the extraction fallback:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./UMML-*.AppImage
```

Also confirm the file is executable with `chmod +x UMML-*.AppImage`.

### Source installer cannot download Micromamba

Confirm DNS and HTTPS connectivity. The installer tries both the Micromamba API
and the official GitHub release asset. An existing `micromamba` executable is
reused automatically.

## Updating

- **DEB:** install the newer DEB with `sudo apt install ./new-package.deb`.
- **AppImage:** replace the old file with the newer AppImage.
- **Source install:** extract the new source and rerun `./install.sh`.

The source installer's private environment is reused and its dependencies are
brought to the pinned versions.

## Uninstalling

- **DEB:** `sudo apt remove umml-linux`
- **AppImage:** delete the AppImage file
- **Source install:** run `./uninstall.sh` from the extracted source package

None of these methods intentionally remove game files, backups, or game metadata
caches.
