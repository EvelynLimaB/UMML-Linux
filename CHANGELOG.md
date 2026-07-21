# Changelog

All notable changes to the Linux/Proton fork are documented here.

## [1.5.0-linux.4] - 2026-07-21

### Fixed

- Manual selection no longer resolves away a Steam symlink before locating the
  associated library and Proton prefix.
- A selected game root can be paired with data stored separately under
  `steamapps/compatdata/3224770`.
- Manual selection accepts the game root, `_Data`, `Persistent`, LocalLow data,
  or the `dat` subfolder.
- When a valid game root is found but its data remains unknown, UMML asks for the
  data folder separately instead of incorrectly rejecting the game folder.

### Validation

- Added the exact symlinked-game/separate-Proton-data regression test.
- DEB and AppImage smoke tests now use a symlinked Steam game directory with
  `meta` and `dat` stored only inside the Proton prefix.

## [1.5.0-linux.3] - 2026-07-21

### Fixed

- Native Linux Mint, Ubuntu, and Debian Steam installs are discovered from
  `~/.steam/debian-installation`.
- Packaged builds retain Steam manifest discovery through a built-in Valve
  KeyValues fallback parser.
- Running Steam/Proton processes and known game-folder names can aid discovery.
- Partial detection is reported more clearly and manual game-folder selection
  is available.

## [1.5.0-linux.2] - 2026-07-21

### Added

- Self-contained x86_64 DEB package for Linux Mint, Ubuntu, and Debian.
- Portable x86_64 AppImage for other Linux distributions.
- Shared PyInstaller runtime, desktop metadata, smoke tests, and checksums.

## [1.5.0-linux.1] - 2026-07-21

### Added

- Native Linux and Steam Proton support for Umamusume Pretty Derby Global.
- Native, Flatpak, and secondary Steam-library discovery.
- Current and legacy Proton data-path detection.
- Resizable ttk interface, diagnostics, `umml-doctor`, logging, tests, and CI.

### Preserved

- Upstream `1.5.0-hotfix` behavior and MIT licensing.
- Windows Steam Global/Japan, DMM Japan, and Komoe Taiwan support.
