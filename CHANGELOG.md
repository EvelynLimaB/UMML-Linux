# Changelog

All notable changes to the Linux/Proton fork are documented here.

## Unreleased

### Added

- Added a Global-client first-run offer and permanent toggle for the optional
  third-party UM:PD Dark Mode package.
- Added an opt-in GameBanana downloader that keeps the original archive outside
  UMML release artifacts and records source, attribution, license, and SHA-256.
- Added dedicated per-mod backups and conflict-aware disable behavior so files
  changed later by another mod are never overwritten silently.
- Added safe ZIP, TAR, and 7z extraction with path traversal and link rejection.
- Added third-party distribution notices and four focused featured-mod tests.

## [1.5.0-linux.6] - 2026-07-21

### Fixed

- Proton LocalLow discovery now resolves `drive_c`, `users`, Windows usernames,
  `AppData`, `LocalLow`, publisher, and game directories case-insensitively.
- Current Steam Global data under `Cygames/Umamusume` is detected on Linux
  filesystems instead of being missed by the older lowercase-only join.
- Bounded sibling scans accept renamed but structurally valid LocalLow data
  directories containing both `meta` and `dat` without recursively crawling the
  entire prefix.

### Validation

- Added direct uppercase/mixed-case LocalLow tests.
- Added an end-to-end Mint manifest + Proton `Cygames/Umamusume` fixture.
- 36 tests, Python compilation, and shell validation pass locally.

## [1.5.0-linux.5] - 2026-07-21

### Changed

- Replaced `umml_detection_hotfix.py`, `umml_manual_location_fix.py`, and
  unreliable project-local `sitecustomize.py` activation with one
  `umml_autodetect` package activated directly by `UMML.py`.
- Steam roots, libraries, game candidates, Proton prefixes, and data candidates
  are now independently discovered and scored before pairing.
- `umml-doctor` now prints detailed evidence and selection reports.

### Added

- Debian/Mint, uppercase/lowercase XDG, legacy native, Flatpak current/legacy,
  Snap normal/hidden, and system Steam-root coverage.
- Old/new `libraryfolders.vdf`, `config/libraryfolders.vdf`, and legacy
  `BaseInstallFolder_*` parsing.
- Runtime `/proc` Steam/Proton environment discovery.
- Case-insensitive Steam directory resolution and symlink-preserving paths.
- Independent cross-library prefix search and newest-prefix selection via
  `pfx.lock` time.
- Standard-library Valve KeyValues fallback parser.
- Behavioral reference documentation for Protontricks, Lutris, and Valve Proton.

## [1.5.0-linux.4] - 2026-07-21

- Fixed manual selection for symlinked games and separate Proton data.

## [1.5.0-linux.3] - 2026-07-21

- Added Mint/Debian Steam discovery and manual game selection.

## [1.5.0-linux.2] - 2026-07-21

- Added self-contained DEB and AppImage packages.

## [1.5.0-linux.1] - 2026-07-21

- Added the initial polished Linux/Steam Proton port.
