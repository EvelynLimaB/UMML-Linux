# Changelog

All notable changes to the Linux/Proton fork are documented here.

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
