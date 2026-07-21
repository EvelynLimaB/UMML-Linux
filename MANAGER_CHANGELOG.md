# UMML Manager changelog

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
