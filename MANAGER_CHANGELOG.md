# UMML Manager changelog

## 0.2.0~alpha4 - 2026-07-22

### Added

- A separate x86_64 AppImage built from the exact same frozen manager runtime as the Debian package.
- AppImage desktop integration metadata, icon, AppStream metadata, GUI entry point, CLI mode, and legacy Studio host.
- CI artifacts for the DEB, AppImage, and a shared external `SHA256SUMS` file.
- AppImage smoke tests for version reporting and CLI startup.
- AppImage extraction checks that compare the embedded manager executable byte-for-byte with the frozen bundle used by the DEB.

### Safety

- ZIP and TAR imports now enforce a 20,000-entry and 8 GiB expanded-size limit before extraction.
- Encrypted ZIP entries and archive special files are rejected.
- Archive member names have a bounded length.
- Temporary imports continue to be removed on every failure path.
- `appimagetool` is downloaded over HTTPS and checked against a pinned SHA-256 before use.

### Packaging

- The Debian and AppImage packages are inspected in the same CI job after one shared PyInstaller build.
- Checksums are generated outside the packages to avoid self-referential package hashes.
- The AppImage can be invoked as a GUI application, with `--version`, or with `--cli` for manager CLI commands.

## 0.2.0~alpha3 - 2026-07-21

### Fixed

- Debian desktop launches now use `/usr/bin/umml-manager` directly so stale user-level PATH entries cannot silently start an older source copy.
- Source application files now live in `~/.local/share/umml-manager-app`; manager library and deployment state remain separately preserved in `~/.local/share/umml-manager`.
- The source installer uses a distinct desktop ID and source-specific launchers. Its compatibility commands prefer the Debian package whenever installed.
- The source uninstaller no longer deletes the manager library, profiles, settings, baselines, transactions, downloads, or workspaces.
- Enabled but unprepared mods now block profile deployment instead of producing a misleading successful no-op.
- Corrupt `active.json`, mod registry, and profile registry files fail closed instead of being silently treated as empty state.
- Re-importing the same mod ID and version with different contents can no longer overwrite immutable source files.
- Different versions of the same logical mod coexist under distinct record IDs instead of replacing the registered version.
- GameBanana result changes now clear stale selections, disable invalid install actions, and honor previous/next page availability.

### Changed

- Conflict plans explicitly list missing and unprepared enabled mods.
- Workspace instructions require a new version or ID before importing edited content.
- GameBanana and local discovery tables now include vertical scrollbars.

## 0.2.0~alpha2 - 2026-07-21

### Fixed

- First launch now invokes the existing Steam, Proton, DMM, and regional installation detector instead of leaving every path field blank.
- Detected encrypted metadata is automatically converted into UMML's validated readable `meta_decrypted_*.db` cache.
- Saved paths are validated at startup and re-detected when missing or stale.
- Background-task error callbacks now capture exceptions safely instead of retaining a cleared Python exception variable.

### Changed

- Settings begins with a guided **Auto-detect installation** action and explains when manual paths are needed.
- Path labels now distinguish the game installation, `Persistent/dat`, and the prepared metadata database.
- Taiwan is retained as a selectable game region even though the GameBanana browser currently exposes Global and Japan catalogues.

## 0.2.0~alpha1 - 2026-07-21

### Added

- Polished dark sidebar interface with Library, Discover, Studio, Conflicts, and Settings workspaces.
- Built-in GameBanana browser for the separate Global and Japan Umamusume listings.
- GameBanana paging, search, sorting, descriptions, authors, versions, statistics, file selection, page links, download, and import.
- Bounded automatic detection of nested mod folders and compatible ZIP/TAR archives.
- Configurable scan roots with Downloads, Documents, and Desktop defaults.
- Editable workspace copies that retain provenance and never mutate immutable imported versions.
- Studio compatibility host containing the full legacy UMML workspace and direct launch cards for character attributes, personality, dresses, training, story concerts, model swaps, translation merge, cleanup, and database reset.
- Game-running guards around mutating legacy Studio actions.
- CLI commands: `scan`, `browse`, `workspace`, and `studio`.

### Changed

- Nested parent folders can now be selected directly; the importer resolves the actual mod root.
- GameBanana metadata records descriptions, version, categories, statistics, previews, and all listed files when available.
- The frozen manager package now bundles the legacy editor backend and modular interface pages.
- Manager version advanced from `0.1.0~alpha1` to `0.2.0~alpha1`.

### Safety

- Local scanning is depth- and entry-limited and skips Steam, Proton, VCS, cache, and dependency directories.
- Archive traversal, links, devices, and unsafe paths remain rejected.
- Studio writes remain blocked while Umamusume is detected.

## 0.1.0~alpha1 - 2026-07-21

- Initial separately packaged manager foundation.
- Immutable mod library and named ordered profiles.
- Deterministic conflict planning and transactional deployment.
- Vanilla baseline and external-change protection.
- Folder, ZIP, TAR, and direct GameBanana import.
- Tk GUI, CLI, tests, frozen runtime, and independent Debian package.
