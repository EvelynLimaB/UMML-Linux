# Changelog

All notable changes to the Linux/Proton fork are documented here.

## [1.5.0-linux.3] - 2026-07-21

### Fixed

- Native Linux Mint, Ubuntu, and Debian Steam installs are now discovered from
  `~/.steam/debian-installation` even when legacy Steam symlinks are absent.
- Packaged DEB/AppImage builds now retain Steam manifest discovery when the
  optional `vdf` parser cannot be imported or rejects a harmless format change.
- Running Steam/Proton processes can supply the real Steam library and game path.
- Known Umamusume folder names are checked when the app manifest is unavailable.
- Permission-restricted `/proc` entries are ignored instead of aborting detection.
- Partial detection is shown more clearly, and failed automatic detection now
  offers manual Steam Global folder selection.

### Validation

- Added an end-to-end fake Linux Mint native Steam layout test.
- Added fallback Valve KeyValues parser tests.
- Added manual-folder and restricted-process tests.
- Release package smoke tests now validate detection, not only `--version`.

## [1.5.0-linux.2] - 2026-07-21

### Added

- Self-contained x86_64 DEB package for Linux Mint, Ubuntu, and Debian.
- Portable x86_64 AppImage for other Linux distributions.
- PyInstaller runtime shared by both binary formats.
- Desktop, icon, AppStream metadata, smoke tests, and release checksums.

## [1.5.0-linux.1] - 2026-07-21

### Added

- Native Linux and Steam Proton support for Umamusume Pretty Derby Global.
- Native, Flatpak, and secondary Steam-library discovery.
- Current and legacy Proton data-path detection.
- Resizable ttk interface, diagnostics, `umml-doctor`, logging, tests, and CI.

### Preserved

- Upstream `1.5.0-hotfix` behavior and MIT licensing.
- Windows Steam Global/Japan, DMM Japan, and Komoe Taiwan support.
