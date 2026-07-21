# Changelog

All notable changes to the Linux/Proton fork are documented here.

## [1.5.0-linux.2] - 2026-07-21

### Added

- Self-contained x86_64 DEB package for Linux Mint, Ubuntu, and Debian.
- Portable x86_64 AppImage for other Linux distributions.
- PyInstaller build definition shared by both binary package formats.
- Desktop, icon, and AppStream metadata for packaged installations.
- Package smoke tests and release checksums for all binary assets.
- `--version` support that works from source, DEB, and AppImage builds.

### Changed

- The release pipeline now builds ZIP, tarball, DEB, and AppImage assets.
- Runtime resource lookup now works from PyInstaller's bundled data directory.

## [1.5.0-linux.1] - 2026-07-21

### Added

- Native Linux and Steam Proton support for Umamusume Pretty Derby Global.
- Native, Flatpak, and secondary Steam-library discovery.
- Current and legacy Proton data-path detection.
- A resizable ttk interface with visible startup progress and diagnostics.
- `umml-doctor`, persistent desktop-launch logs, and explicit path overrides.
- A user-local Micromamba installer suitable for Bazzite and Fedora Atomic.
- Automated platform-discovery tests, CI checks, and reproducible release archives.

### Preserved

- Upstream `1.5.0-hotfix` loader behavior.
- Windows Steam Global and Steam Japan discovery.
- DMM Japan and Komoe Taiwan support.
- Existing credits and MIT licensing.

### Notes

Linux with Steam Global through Proton is the primary manually tested target.
Windows and other regional layouts are retained but should receive additional
manual regression testing before large upstream changes are merged.
