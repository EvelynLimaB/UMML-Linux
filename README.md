# UMML Linux

[![Latest release](https://img.shields.io/github/v/release/EvelynLimaB/UMML-Linux?display_name=tag&sort=semver)](https://github.com/EvelynLimaB/UMML-Linux/releases/latest)
[![Python checks](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml/badge.svg)](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-7651a8.svg)](LICENSE)

A maintained Linux/Steam Proton port of **UMML**, the desktop mod loader for
**Umamusume Pretty Derby**. UMML can inspect mod packages, create backups, load
replacement assets, preview supported assets, and restore original game files.

**Current release:** `1.5.0-linux.1`, based on upstream `1.5.0-hotfix`.

## Download

Use the packaged ZIP or tarball from the
[latest release](https://github.com/EvelynLimaB/UMML-Linux/releases/latest).
Release assets include `SHA256SUMS` for verification.

The horse game has successfully entered the penguin machine. `ฅ^•ﻌ•^ฅ`

## Supported installations

| Installation | Detection | Status |
| --- | --- | --- |
| Steam Global | Windows Steam, native Linux Steam, Flatpak Steam, secondary libraries, Proton | Supported and Linux-tested |
| Steam Japan | Steam app manifest | Supported |
| DMM Japan | DMM Game Player configuration | Supported on Windows |
| Komoe Taiwan | Windows uninstall registry or explicit override | Supported |
| Kakao Korea | — | Not implemented upstream |

Steam Global uses app ID `3224770`; Steam Japan uses `3564400`.

## Linux / Steam Proton

The installer creates a private Python 3.11/Tk environment inside your user
account. It does not modify the system Python, require `rpm-ostree`, or require a
reboot, making it suitable for Bazzite and Fedora Atomic systems.

```bash
chmod +x install.sh
./install.sh
umml-doctor
umml
```

A desktop application named **UMML** is installed automatically. Detailed path
overrides, Flatpak notes, logs, updating, and troubleshooting are documented in
[docs/LINUX.md](docs/LINUX.md).

## Windows

1. Install Python 3.11 or newer with Tk support.
2. Download and extract the release ZIP.
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
The Linux uninstaller deliberately leaves game data and backups untouched.

## Diagnostics

```bash
python UMML.py --version
python UMML.py --doctor
```

After Linux installation:

```bash
umml-doctor
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
UMML.py                  Cross-platform entry point and refreshed interface
UMML_core.py             Preserved upstream loader implementation
umml_platform.py         Platform discovery and installation chooser
UMML_data/dropdown.json  UI data used by training/cut-in controls
install.sh               Linux user-local installer
uninstall.sh             Linux uninstaller
scripts/build_release.sh Reproducible ZIP/tarball builder
requirements.txt         Tested Python dependency versions
tests/                   Discovery and release-contract regression tests
docs/LINUX.md            Linux and Proton guide
```

## Development

```bash
python -m py_compile UMML.py UMML_core.py umml_platform.py
python -m unittest discover -s tests -v
bash -n install.sh uninstall.sh scripts/build_release.sh
scripts/build_release.sh
```

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
