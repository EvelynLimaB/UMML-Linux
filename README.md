# UMML Linux

[![Latest release](https://img.shields.io/github/v/release/EvelynLimaB/UMML-Linux?display_name=tag&sort=semver)](https://github.com/EvelynLimaB/UMML-Linux/releases/latest)
[![Python checks](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml/badge.svg)](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-7651a8.svg)](LICENSE)

A maintained Linux/Steam Proton port of **UMML**, the desktop mod loader for
**Umamusume Pretty Derby**. UMML can inspect mod packages, create backups, load
replacement assets, preview supported assets, and restore original game files.

**Current release:** `1.5.0-linux.2`, based on upstream `1.5.0-hotfix`.

## Download

Use the assets attached to the
[latest release](https://github.com/EvelynLimaB/UMML-Linux/releases/latest):

| Linux setup | Recommended file | How to run |
| --- | --- | --- |
| Linux Mint, Ubuntu, Debian | `umml-linux_1.5.0-linux.2_amd64.deb` | `sudo apt install ./umml-linux_1.5.0-linux.2_amd64.deb` |
| Other x86_64 distributions | `UMML-1.5.0-linux.2-x86_64.AppImage` | `chmod +x *.AppImage && ./UMML-*.AppImage` |
| Source/user-local fallback | ZIP or tarball | extract and run `./install.sh` |

The DEB and AppImage are self-contained: they include Python, Tk, and UMML's
Python dependencies. Users do not need to install Micromamba or pip packages.
Every release also includes `SHA256SUMS`.

The horse game has successfully entered the penguin machine. `ฅ^•ﻌ•^ฅ`

## Package notes

### Linux Mint / Ubuntu / Debian

Install the DEB:

```bash
sudo apt install ./umml-linux_1.5.0-linux.2_amd64.deb
umml-doctor
umml
```

Remove it later with:

```bash
sudo apt remove umml-linux
```

### Portable AppImage

```bash
chmod +x UMML-1.5.0-linux.2-x86_64.AppImage
./UMML-1.5.0-linux.2-x86_64.AppImage
```

On systems without FUSE 2, AppImage's extraction fallback can be used:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./UMML-1.5.0-linux.2-x86_64.AppImage
```

The binary packages currently target **x86_64**, matching the supported Steam
and Proton game setup. The source installer remains available for other Linux
architectures where its dependencies are available.

## Supported installations

| Installation | Detection | Status |
| --- | --- | --- |
| Steam Global | Windows Steam, native Linux Steam, Flatpak Steam, secondary libraries, Proton | Supported and Linux-tested |
| Steam Japan | Steam app manifest | Supported |
| DMM Japan | DMM Game Player configuration | Supported on Windows |
| Komoe Taiwan | Windows uninstall registry or explicit override | Supported |
| Kakao Korea | — | Not implemented upstream |

Steam Global uses app ID `3224770`; Steam Japan uses `3564400`.

## Source installer

The extracted ZIP/tarball includes `install.sh`, which creates a private
Python 3.11/Tk environment inside the current user account. It does not modify
the system Python, require `rpm-ostree`, or require a reboot.

```bash
chmod +x install.sh
./install.sh
umml-doctor
umml
```

Detailed path overrides, Flatpak notes, logs, updating, and troubleshooting are
in [docs/LINUX.md](docs/LINUX.md).

## Windows

1. Install Python 3.11 or newer with Tk support.
2. Download and extract the source ZIP.
3. Install dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Start UMML:

   ```powershell
   py UMML.py
   ```

Keep `UMML.py`, `UMML_core.py`, `umml_platform.py`, `VERSION`, and
`UMML_data/` together.

## Using UMML

1. Launch the game once and allow its initial data download to finish.
2. Close the game.
3. Start UMML and select a detected installation.
4. Browse to an extracted mod folder containing `setting.json`.
5. Review the mod information and preview supported assets.
6. Select **Load mod assets**.
7. Use **Restore original assets** before troubleshooting or applying a game
   update when practical.

UMML creates its asset backup beside the selected game data as `dat.backup`.
Removing UMML does not delete game data or backups.

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
metadata/data paths, write access, and Python dependencies. The same report is
available from **Help → Run diagnostics**.

## Path overrides

| Variable | Meaning |
| --- | --- |
| `UMML_STEAM_ROOT` | Steam root containing `steamapps/` |
| `UMML_GAME_DIR` | Steam Global game installation directory |
| `UMML_GAME_DIR_3224770` | Steam Global game directory |
| `UMML_GAME_DIR_3564400` | Steam Japan game directory |
| `UMML_PERSISTENT_DIR` | Folder containing `meta`, `dat`, and usually `master/` |
| `UMML_KOMOE_GAME_DIR` | Komoe game directory containing `meta` and `dat/` |
| `UMML_PLATFORM` | Skip the chooser: `steam-global`, `steam-japan`, `dmm-japan`, or `komoe-tw` |

Example:

```bash
UMML_GAME_DIR="$HOME/Games/Umamusume Pretty Derby" \
UMML_PERSISTENT_DIR="/mnt/games/uma-persistent" \
umml
```

`UMML_PERSISTENT_DIR` points to the parent of `dat/`, not to `dat/` itself.

## Project structure

```text
UMML.py                       Cross-platform entry point and refreshed interface
UMML_core.py                  Preserved upstream loader implementation
umml_platform.py              Platform discovery and installation chooser
UMML_data/dropdown.json       UI data used by training/cut-in controls
install.sh                    Source-based user-local Linux installer
packaging/                    Desktop, AppStream, and PyInstaller definitions
scripts/build_frozen.sh       Self-contained runtime builder
scripts/build_deb.sh          Linux Mint/Ubuntu/Debian package builder
scripts/build_appimage.sh     Portable AppImage builder
scripts/build_release.sh      Source ZIP/tarball builder
requirements*.txt             Runtime and build dependency pins
tests/                        Discovery and release-contract regression tests
docs/LINUX.md                 Linux and Proton guide
```

## Development

```bash
python -m py_compile UMML.py UMML_core.py umml_platform.py umml_packaged.py
python -m unittest discover -s tests -v
bash -n install.sh uninstall.sh scripts/*.sh
scripts/build_release.sh
```

Building the self-contained packages also requires the packages in
`requirements-build.txt`, `dpkg-deb`, and `appimagetool`.

See [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), and
[SECURITY.md](SECURITY.md).

## Safety

Keep the game closed while UMML writes or restores assets. Modding an online
game may be restricted by its terms or affected by future game/anti-cheat
updates. UMML is provided without warranty; maintain your own backups and use it
at your own risk.

## Credits

- [tumugu](https://github.com/tumugu) — original mod loader
- [noccu](https://github.com/noccu) — [hachimi-tools](https://github.com/noccu/hachimi-tools) metadata decryption
- [kairusds](https://github.com/kairusds) — [umamusu-utils](https://github.com/kairusds/umamusu-utils) asset decryption
- [teiosteppa](https://github.com/teiosteppa) — [umamusume-model-replace](https://github.com/teiosteppa/umamusume-model-replace) reference
- [qwcan](https://github.com/qwcan) — [UmaLauncher](https://github.com/qwcan/UmaLauncher) DMM path reference
- NaufalFajri and upstream contributors — current UMML implementation and regional support

## License

MIT. See [LICENSE](LICENSE). Preserve the copyright and permission notice in
copies or substantial portions of the software.
