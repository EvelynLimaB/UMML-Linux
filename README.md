# UMML Linux

[![Latest release](https://img.shields.io/github/v/release/EvelynLimaB/UMML-Linux?display_name=tag&sort=semver)](https://github.com/EvelynLimaB/UMML-Linux/releases/latest)
[![Python checks](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml/badge.svg)](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-7651a8.svg)](LICENSE)

A maintained Linux/Steam Proton port of **UMML**, the desktop mod loader for
**Umamusume Pretty Derby**.

**Current release:** `1.5.0-linux.6`, based on upstream `1.5.0-hotfix`.

## Download

| Linux setup | Recommended file | Install or run |
| --- | --- | --- |
| Linux Mint, Ubuntu, Debian | `umml-linux_1.5.0-linux.6_amd64.deb` | `sudo apt install ./umml-linux_1.5.0-linux.6_amd64.deb` |
| Other x86_64 distributions | `UMML-1.5.0-linux.6-x86_64.AppImage` | `chmod +x *.AppImage && ./UMML-*.AppImage` |
| Source/user-local fallback | ZIP or tarball | extract and run `./install.sh` |

Use the assets attached to the
[latest release](https://github.com/EvelynLimaB/UMML-Linux/releases/latest).
The binary packages are self-contained and every release includes
`SHA256SUMS`.

The horse game has successfully entered the penguin machine. `ฅ^•ﻌ•^ฅ`

## Autodetection v2

`1.5.0-linux.5` replaced the layered path hotfixes with one scored discovery
engine. It independently discovers and pairs:

- native Debian/Mint, XDG and legacy Steam clients;
- Flatpak and Snap Steam layouts;
- every modern or legacy secondary Steam library;
- the game through process environment, manifest, or marker scan;
- game-local Persistent data and every matching Proton prefix;
- game and prefix locations even when they live on different libraries;
- symlinked and case-mismatched Steam paths;
- the newest valid prefix when duplicate `compatdata` folders exist.

`1.5.0-linux.6` fixes the final Global-client edge case: Wine paths are
case-insensitive, but Linux filesystems are not. LocalLow discovery now resolves
every path component case-insensitively and accepts current
`Cygames/Umamusume`, older `Cygames/umamusume`, and other bounded valid siblings
containing both `meta` and `dat`.

`umml-doctor` lists every candidate, score, evidence source, selected game,
selected data directory, and final readiness result. See
[docs/AUTODETECTION.md](docs/AUTODETECTION.md) for the design and the
Protontricks, Lutris, Valve Proton, and UmaViewer references.

## Mint / Ubuntu / Debian

```bash
sudo apt install ./umml-linux_1.5.0-linux.6_amd64.deb
umml-doctor
umml
```

Installing a newer DEB upgrades the existing package. Remove it with:

```bash
sudo apt remove umml-linux
```

## AppImage

```bash
chmod +x UMML-1.5.0-linux.6-x86_64.AppImage
./UMML-1.5.0-linux.6-x86_64.AppImage
```

Without FUSE 2:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./UMML-1.5.0-linux.6-x86_64.AppImage
```

## Source installer

```bash
chmod +x install.sh
./install.sh
umml-doctor
umml
```

The source installer creates an isolated user-local Python/Tk environment and
leaves the system Python untouched.

## Supported installations

| Installation | Status |
| --- | --- |
| Steam Global, native Windows or Linux/Proton | Supported; Linux tested |
| Steam Japan | Supported |
| DMM Japan | Supported on Windows |
| Komoe Taiwan | Supported on Windows |
| Kakao Korea | Not implemented upstream |

Steam Global uses app ID `3224770`; Steam Japan uses `3564400`.

## Using UMML

1. Launch the game once and let its data download finish.
2. Close the game before writing or restoring assets.
3. Run `umml-doctor`; the final autodetect result should be `READY`.
4. Start `umml` and select an extracted mod folder containing `setting.json`.
5. Load or restore assets.

When automatic pairing cannot finish, UMML accepts either the game root or the
data folder first, then asks for the missing half. Valid data folders contain
both `meta` and `dat`.

## Optional UM:PD Dark Mode

For the Global client, UMML can offer **UM:PD Dark Mode** once after startup.
Accepting the offer downloads the creator's original archive directly from its
GameBanana page and installs it through a dedicated reversible backup. The
archive itself is not included in UMML releases.

The permanent **Featured optional mod** switch can enable or disable it later.
When disabling, UMML restores only files that still match the version it
installed. A file subsequently changed by another mod is left untouched and
reported as a conflict instead of being overwritten.

The publisher states `CC BY-NC-ND 4.0`. Source, attribution, license, local state
path, and the downloaded archive's SHA-256 are visible from the interface. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the distribution boundary.

## Overrides

| Variable | Meaning |
| --- | --- |
| `UMML_STEAM_ROOT` | Steam root containing `steamapps/` |
| `UMML_GAME_DIR` | Steam Global game directory |
| `UMML_GAME_DIR_3224770` | Steam Global game directory |
| `UMML_GAME_DIR_3564400` | Steam Japan game directory |
| `UMML_PERSISTENT_DIR` | Data directory containing `meta` and `dat/` |
| `UMML_PLATFORM` | Force a supported platform key |

## Development

```bash
python -m py_compile UMML.py UMML_core.py umml_platform.py umml_packaged.py umml_entry.py umml_featured_mods.py umml_featured_ui.py umml_autodetect/*.py
python -m unittest discover -s tests -v
bash -n install.sh uninstall.sh scripts/*.sh
scripts/build_release.sh
```

See [docs/LINUX.md](docs/LINUX.md), [CONTRIBUTING.md](CONTRIBUTING.md),
[CHANGELOG.md](CHANGELOG.md), and [SECURITY.md](SECURITY.md).

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

MIT. See [LICENSE](LICENSE). Third-party downloads remain under their respective
licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
