# UMML Linux

[![Latest release](https://img.shields.io/github/v/release/EvelynLimaB/UMML-Linux?display_name=tag&sort=semver)](https://github.com/EvelynLimaB/UMML-Linux/releases/latest)
[![Python checks](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml/badge.svg)](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-7651a8.svg)](LICENSE)

A maintained Linux/Steam Proton port of **UMML**, the desktop mod loader for
**Umamusume Pretty Derby**. UMML can inspect mod packages, create backups, load
replacement assets, preview supported assets, and restore original game files.

**Current release:** `1.5.0-linux.3`, based on upstream `1.5.0-hotfix`.

## Download

Use the assets attached to the
[latest release](https://github.com/EvelynLimaB/UMML-Linux/releases/latest):

| Linux setup | Recommended file | How to run |
| --- | --- | --- |
| Linux Mint, Ubuntu, Debian | `umml-linux_1.5.0-linux.3_amd64.deb` | `sudo apt install ./umml-linux_1.5.0-linux.3_amd64.deb` |
| Other x86_64 distributions | `UMML-1.5.0-linux.3-x86_64.AppImage` | `chmod +x *.AppImage && ./UMML-*.AppImage` |
| Source/user-local fallback | ZIP or tarball | extract and run `./install.sh` |

The DEB and AppImage are self-contained: they include Python, Tk, and UMML's
Python dependencies. Every release includes `SHA256SUMS`.

The horse game has successfully entered the penguin machine. `ฅ^•ﻌ•^ฅ`

## Mint detection hotfix

`1.5.0-linux.3` fixes the packaged build failing to see a visibly running game on
Linux Mint. Detection now checks:

- `~/.steam/debian-installation`, used by native Mint/Ubuntu/Debian Steam;
- native, Flatpak, Snap, XDG, and secondary Steam libraries;
- running Steam and Proton process paths;
- known Umamusume installation folder names when a manifest is unavailable;
- a built-in Valve KeyValues fallback parser for frozen packages.

When automatic detection still fails, UMML now offers to locate the Steam Global
game folder manually. Select the folder containing `UmamusumePrettyDerby_Data`.

## Install on Linux Mint / Ubuntu / Debian

```bash
sudo apt install ./umml-linux_1.5.0-linux.3_amd64.deb
umml-doctor
umml
```

Remove it later with:

```bash
sudo apt remove umml-linux
```

## Portable AppImage

```bash
chmod +x UMML-1.5.0-linux.3-x86_64.AppImage
./UMML-1.5.0-linux.3-x86_64.AppImage
```

On systems without FUSE 2:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./UMML-1.5.0-linux.3-x86_64.AppImage
```

Binary packages currently target **x86_64**. The source installer remains
available for other Linux architectures where its dependencies are available.

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

The source ZIP/tarball includes a user-local installer that creates a private
Python 3.11/Tk environment without modifying system Python:

```bash
chmod +x install.sh
./install.sh
umml-doctor
umml
```

Detailed path overrides, Flatpak notes, logs, updating, and troubleshooting are
in [docs/LINUX.md](docs/LINUX.md).

## Windows

```powershell
py -m pip install -r requirements.txt
py UMML.py
```

Keep `UMML.py`, `UMML_core.py`, `umml_platform.py`, `VERSION`, and
`UMML_data/` together.

## Using UMML

1. Launch the game once and allow its initial data download to finish.
2. Close the game before loading or restoring assets.
3. Start UMML and select a detected installation.
4. When automatic detection fails, accept the manual folder prompt.
5. Browse to an extracted mod folder containing `setting.json`.
6. Review the mod information, then select **Load mod assets**.
7. Use **Restore original assets** before troubleshooting or game updates when practical.

UMML creates its backup beside the selected game data as `dat.backup`. Removing
UMML does not delete game data or backups.

## Diagnostics

```bash
umml --version
umml-doctor
```

From source:

```bash
python UMML.py --version
python UMML.py --doctor
```

The report lists Steam roots, secondary libraries, detected installations,
metadata/data paths, write access, and Python dependencies.

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
python -m py_compile UMML.py UMML_core.py umml_platform.py umml_detection_hotfix.py sitecustomize.py umml_packaged.py
python -m unittest discover -s tests -v
bash -n install.sh uninstall.sh scripts/*.sh
scripts/build_release.sh
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), and
[SECURITY.md](SECURITY.md).

## Safety

Keep the game closed while UMML writes or restores assets. Modding an online
game may be restricted by its terms or affected by future game/anti-cheat
updates. UMML is provided without warranty; maintain backups and use it at your
own risk.

## Credits

- [tumugu](https://github.com/tumugu) — original mod loader
- [noccu](https://github.com/noccu) — [hachimi-tools](https://github.com/noccu/hachimi-tools) metadata decryption
- [kairusds](https://github.com/kairusds) — [umamusu-utils](https://github.com/kairusds/umamusu-utils) asset decryption
- [teiosteppa](https://github.com/teiosteppa) — [umamusume-model-replace](https://github.com/teiosteppa/umamusume-model-replace) reference
- [qwcan](https://github.com/qwcan) — [UmaLauncher](https://github.com/qwcan/UmaLauncher) DMM path reference
- NaufalFajri and upstream contributors — current UMML implementation and regional support

## License

MIT. See [LICENSE](LICENSE).
