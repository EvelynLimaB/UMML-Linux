# UMML Linux

[![Latest release](https://img.shields.io/github/v/release/EvelynLimaB/UMML-Linux?display_name=tag&sort=semver)](https://github.com/EvelynLimaB/UMML-Linux/releases/latest)
[![Python checks](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml/badge.svg)](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-7651a8.svg)](LICENSE)

A maintained Linux/Steam Proton port of **UMML**, the desktop mod loader for
**Umamusume Pretty Derby**.

**Current release:** `1.5.0-linux.4`, based on upstream `1.5.0-hotfix`.

## Download

Use the assets attached to the
[latest release](https://github.com/EvelynLimaB/UMML-Linux/releases/latest):

| Linux setup | Recommended file | How to run |
| --- | --- | --- |
| Linux Mint, Ubuntu, Debian | `umml-linux_1.5.0-linux.4_amd64.deb` | `sudo apt install ./umml-linux_1.5.0-linux.4_amd64.deb` |
| Other x86_64 distributions | `UMML-1.5.0-linux.4-x86_64.AppImage` | `chmod +x *.AppImage && ./UMML-*.AppImage` |
| Source/user-local fallback | ZIP or tarball | extract and run `./install.sh` |

The DEB and AppImage are self-contained and include Python, Tk, and UMML's
Python dependencies. Every release includes `SHA256SUMS`.

The horse game has successfully entered the penguin machine. `ฅ^•ﻌ•^ฅ`

## Manual location fix in `.4`

The `.3` chooser wrongly rejected a valid game root when Steam exposed the game
through a symlink and Proton kept `meta`/`dat` separately under
`compatdata/3224770`. `.4` preserves the selected symlink path and scans every
known Steam library for the matching Proton data.

The manual chooser now accepts:

- the game root containing `UmamusumePrettyDerby_Data`;
- the `UmamusumePrettyDerby_Data` folder itself;
- the current `Persistent` folder;
- the Proton `LocalLow/Cygames/umamusume` folder;
- its `dat` subfolder.

When the selected game root is valid but its data cannot be found automatically,
UMML asks for the data folder separately instead of declaring the game folder
incompatible.

## Linux Mint / Ubuntu / Debian

```bash
sudo apt install ./umml-linux_1.5.0-linux.4_amd64.deb
umml-doctor
umml
```

The package upgrades older UMML Linux DEBs in place.

## Portable AppImage

```bash
chmod +x UMML-1.5.0-linux.4-x86_64.AppImage
./UMML-1.5.0-linux.4-x86_64.AppImage
```

Without FUSE 2:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./UMML-1.5.0-linux.4-x86_64.AppImage
```

## Supported installations

| Installation | Detection | Status |
| --- | --- | --- |
| Steam Global | Windows Steam, native Linux Steam, Mint/Debian Steam, Flatpak, Snap, secondary libraries, Proton | Supported and Linux-tested |
| Steam Japan | Steam manifest or known folder | Supported |
| DMM Japan | DMM Game Player configuration | Supported on Windows |
| Komoe Taiwan | Windows uninstall registry or explicit override | Supported |
| Kakao Korea | — | Not implemented upstream |

Steam Global uses app ID `3224770`; Steam Japan uses `3564400`.

## Source installer

```bash
chmod +x install.sh
./install.sh
umml-doctor
umml
```

Detailed path overrides, logs, Flatpak notes, and troubleshooting are in
[docs/LINUX.md](docs/LINUX.md).

## Using UMML

1. Launch the game once and let its initial data download finish.
2. Close the game before loading or restoring assets.
3. Start UMML and select the detected installation.
4. When automatic detection fails, locate the game root.
5. When UMML asks for data separately, select `Persistent` or
   `LocalLow/Cygames/umamusume`—the folder containing both `meta` and `dat`.
6. Select an extracted mod folder containing `setting.json`.
7. Load or restore assets.

UMML creates `dat.backup` beside the selected game data. Removing UMML does not
delete game files or backups.

## Diagnostics

```bash
umml --version
umml-doctor
```

## Path overrides

| Variable | Meaning |
| --- | --- |
| `UMML_STEAM_ROOT` | Steam root containing `steamapps/` |
| `UMML_GAME_DIR` | Steam Global game installation directory |
| `UMML_GAME_DIR_3224770` | Steam Global game directory |
| `UMML_GAME_DIR_3564400` | Steam Japan game directory |
| `UMML_PERSISTENT_DIR` | Folder containing `meta`, `dat`, and usually `master/` |
| `UMML_KOMOE_GAME_DIR` | Komoe game directory containing `meta` and `dat/` |
| `UMML_PLATFORM` | `steam-global`, `steam-japan`, `dmm-japan`, or `komoe-tw` |

## Development

```bash
python -m py_compile \
  UMML.py UMML_core.py umml_platform.py \
  umml_detection_hotfix.py umml_manual_location_fix.py \
  sitecustomize.py umml_packaged.py
python -m unittest discover -s tests -v
bash -n install.sh uninstall.sh scripts/*.sh
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), and
[SECURITY.md](SECURITY.md).

## Safety

Keep the game closed while UMML writes or restores assets. Maintain backups and
use mods at your own risk.

## Credits

- [tumugu](https://github.com/tumugu) — original mod loader
- [noccu](https://github.com/noccu) — metadata decryption reference
- [kairusds](https://github.com/kairusds) — asset decryption reference
- [teiosteppa](https://github.com/teiosteppa) — model replacement reference
- [qwcan](https://github.com/qwcan) — DMM path reference
- NaufalFajri and upstream contributors — current UMML implementation and regional support

## License

MIT. See [LICENSE](LICENSE).
