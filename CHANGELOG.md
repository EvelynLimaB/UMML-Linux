# Changelog

All notable changes to the Linux/Proton fork are documented here.

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
- 16 autodetection fixtures plus existing platform and release tests.
- Behavioral reference documentation for Protontricks, Lutris, and Valve Proton.

### Validation

- 31 tests pass locally.
- Source compilation, shell validation, ZIP/tarball builds and archive integrity
  pass locally.
- Release CI installs and tests both the finished DEB and AppImage against a
  symlinked game on one secondary library and a Proton prefix on another.

## [1.5.0-linux.4] - 2026-07-21

- Fixed manual selection for symlinked games and separate Proton data.

## [1.5.0-linux.3] - 2026-07-21

- Added Mint/Debian Steam discovery and manual game selection.

## [1.5.0-linux.2] - 2026-07-21

- Added self-contained DEB and AppImage packages.

## [1.5.0-linux.1] - 2026-07-21

- Added the initial polished Linux/Steam Proton port.
