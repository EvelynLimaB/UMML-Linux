# Linux and Steam Proton guide

## What the installer does

`install.sh` installs UMML entirely inside the current user account:

- application files: `${XDG_DATA_HOME:-~/.local/share}/umml`
- launchers: `~/.local/bin/umml` and `~/.local/bin/umml-doctor`
- desktop entry: `${XDG_DATA_HOME:-~/.local/share}/applications/umml.desktop`
- desktop-launch log: `${XDG_STATE_HOME:-~/.local/state}/umml/umml.log`

It downloads Micromamba from an official source and creates an isolated Python
3.11 environment containing Tk and the pinned Python dependencies. This avoids
`rpm-ostree`, system Python modification, and reboot requirements on Bazzite,
Fedora Atomic, and similar systems.

## Installation

```bash
unzip UMML-Linux.zip
cd UMML-Linux
chmod +x install.sh uninstall.sh
./install.sh
```

Ensure `~/.local/bin` is in `PATH`. Logging out and back in may be necessary on
unusual desktop configurations, but UMML itself does not require a reboot.

## First launch

1. Start Umamusume Pretty Derby Global through Steam.
2. Let the game finish its initial data download.
3. Close the game.
4. Run:

   ```bash
   umml-doctor
   ```

5. Confirm that at least one installation is marked `[OK]` and the report ends
   in `RESULT: READY`.
6. Run `umml` or select UMML from the desktop application menu.

## Steam layouts detected automatically

- native Steam: `~/.local/share/Steam`
- legacy native Steam: `~/.steam/steam` and `~/.steam/root`
- Flatpak Steam: `~/.var/app/com.valvesoftware.Steam/.local/share/Steam`
- every secondary library listed in `libraryfolders.vdf`
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

## Flatpak permissions

UMML itself is not installed as a Flatpak. It reads the Steam Flatpak's files
from your home directory. Secondary libraries mounted outside the home directory
must be readable and writable by the current user.

Check access with:

```bash
namei -l /path/to/SteamLibrary
findmnt /path/to/SteamLibrary
```

A library mounted read-only cannot be used for mod loading or restoration.

## Logs and troubleshooting

Terminal launches print errors directly. Desktop launches append output to:

```text
~/.local/state/umml/umml.log
```

Useful commands:

```bash
umml-doctor
tail -n 200 ~/.local/state/umml/umml.log
```

### No Steam root detected

Set `UMML_STEAM_ROOT` to the directory containing `steamapps/`, then rerun the
doctor.

### Game found but metadata/data missing

Launch the game once and wait for its data download to finish. If the files are
in a nonstandard location, set `UMML_PERSISTENT_DIR` to their parent directory.

### Blank or apparently frozen window

This port creates the primary Tk root only once, parents the platform chooser to
it, and renders startup progress before scanning/decrypting metadata. Check the
log if the status stops changing.

### Installer cannot download Micromamba

Confirm DNS and HTTPS connectivity. The installer tries both the Micromamba API
and the official GitHub release asset. An existing `micromamba` executable is
reused automatically.

## Updating

Pull or extract the new source, then rerun:

```bash
./install.sh
```

The private environment is reused and dependencies are brought to the pinned
versions.

## Uninstalling

```bash
./uninstall.sh
```

This removes the application, launchers, desktop entry, and private environment.
It does not touch game files, `dat.backup`, or game metadata caches.
