# UMML 1.5.0 Linux/Proton 2

The penguin machine now comes in convenient little boxes. `ฅ^•ﻌ•^ฅ`

This release adds self-contained Linux packages on top of the polished
Linux/Steam Proton port based on upstream `1.5.0-hotfix`.

## Pick your package

- **Linux Mint / Ubuntu / Debian:** install the `.deb` with
  `sudo apt install ./umml-linux_1.5.0-linux.2_amd64.deb`.
- **Other x86_64 Linux distributions:** download the `.AppImage`, make it
  executable, and run it directly.
- **Source/user-local installation:** ZIP and tarball packages remain available.

The DEB and AppImage bundle Python, Tk, UnityPy, APSW SQLite3MC, PyYAML, and the
remaining runtime dependencies. They do not need Micromamba or a separate pip
installation.

## Existing highlights

- Steam Global detection on native Steam, Flatpak Steam, and secondary libraries
- Proton-prefix discovery with current and legacy data-layout support
- desktop launcher, persistent logs, and `umml-doctor`
- refreshed resizable interface with startup progress and path diagnostics
- Windows, Steam Japan, DMM Japan, and Komoe Taiwan behavior retained

## Validation

- Python source compilation
- platform-discovery and release-contract regression tests
- PyInstaller frozen-runtime version smoke test
- DEB structure and installed executable smoke test on Ubuntu 22.04
- AppImage extraction-and-run smoke test
- shell validation for all packaging scripts
- SHA-256 checksums for every release asset

Binary packages currently target x86_64. See `docs/LINUX.md` for source installs,
path overrides, Flatpak notes, and troubleshooting.
