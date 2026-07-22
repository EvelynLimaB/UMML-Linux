# UMML Manager changelog

## 0.2.0~alpha9 - 2026-07-22

### Import and preparation

- Compatible legacy UMML asset packages are prepared automatically immediately after import when the detected metadata database is available.
- A failed preparation no longer discards the downloaded or imported source; the mod remains safely in Library and can be retried with **Prepare now**.
- Applying a profile remains a separate explicit action and still requires the game to be closed.
- Provider-confirmed GameBanana archives that contain valid loose UnityFS/audio/video/hash payloads but omit the modern `assets/` wrapper are normalized into an immutable UMML package automatically.

### Safety

- Loose-archive normalization is limited to the GameBanana provider path and requires recognizable game-asset evidence.
- Archives containing executable, script, or native-library payloads are rejected instead of being wrapped as ordinary assets.
- Plain documents and unrelated ZIP files remain unrecognized rather than being imported optimistically.

### Tests

- Added integration coverage for the loose legacy archive shape seen in existing UM:PD GameBanana uploads.
- Added rejection tests for document-only and executable-bearing archives.
- Added policy tests for automatic preparation eligibility.

## 0.2.0~alpha8 - 2026-07-22

### Fixed

- Selecting a GameBanana catalogue row no longer leaves **Install** disabled merely because the index response omitted full downloadable-file metadata.
- The selected submission now fetches its detail record in a dedicated background task and replaces the fallback with the actual file selector when available.
- **Install latest** remains usable while details are loading or when prefetch fails; installation retries the detail endpoint instead of treating an incomplete catalogue row as a submission with no files.
- Stale detail responses are discarded after selection changes, page changes, or shutdown.
- GameBanana file containers are normalized from arrays, numeric-keyed objects, and nested containers before file selection.
- The interactive install path now uses the same preview-aware provider used by browsing and the provider registry.

### Tests

- Added regression coverage for mapping-shaped and nested GameBanana file containers.
- Retained the dependency-complete manager suite, structural audit, package parity checks, and legacy validation.

## 0.2.0~alpha7 - 2026-07-22

### Triple-audit corrections

- Manager regression CI now installs the complete pinned runtime dependency set before running tests, so Pillow-backed preview tests cannot silently skip in the manager workflow.
- The default provider registry now registers the preview-aware GameBanana client instead of the legacy metadata-only client.
- Provider integration tests verify that real GameBanana media fields are normalized through the registered client, not merely through an isolated helper.
- Package inspection now checks for Pillow's compiled imaging extension in both the DEB and AppImage as well as the existing full-runtime parity comparison.
- Dependency installation is followed by `pip check` in both test and packaging jobs.

### Documentation and release preparation

- Preview images are recorded as implemented; persistent offline image caching and before/after comparison remain roadmap items.
- The release checklist now distinguishes completed region/dependency planning support from missing GUI and automatic-install workflows.
- Alpha7 is a distinct package version so corrected artifacts cannot be confused with the previously distributed alpha6 binary.

## 0.2.0~alpha6 - 2026-07-22

### Audit and verification

- Added a standard-library AST audit for syntax, duplicate definitions, mutable defaults, bare exceptions, dangerous deserialization/extraction calls, `shell=True`, and core-layer import violations.
- Expanded regression coverage with adversarial path, archive, immutable-source, provider, schema, baseline, recovery-snapshot, metadata-freshness, installation-binding, and failure-injection tests.
- CI now separates compile, architecture audit, regression tests, metadata validation, frozen builds, package inspection, and full DEB/AppImage runtime-tree parity.
- Failed regression runs upload their complete test log instead of leaving the useful traceback buried under runner setup output.

### Deployment and recovery

- Managed manifest, active-state, baseline, and recovery-journal paths are normalized and required to remain under their declared roots.
- Prepared files are SHA-256 verified before deployment, and installed targets are verified after atomic replacement.
- Active state and vanilla baselines are bound to a specific canonical `Persistent/dat` target so another installation cannot reuse them accidentally.
- Deployment uses cross-process locks and durable transaction journals with snapshot, apply, and commit phases.
- Interrupted transactions are recovered before another profile is applied; unreadable or tampered recovery material fails closed.
- Recovery snapshots and vanilla baseline files now have independent SHA-256 integrity records.
- Snapshot failures before mutation clean up without pretending a rollback failed.
- Future active-state, registry, profile, journal, and baseline schema versions are rejected explicitly.

### Imports, providers, and preparation

- Local folder imports reject symbolic links and special files, enforce file/byte limits, and verify the copied tree still matches the pre-copy digest.
- Mod version text no longer directly controls filesystem paths; display versions and safe storage components are separate.
- Automatic discovery no longer treats every ZIP or ordinary `setting.json` as a mod.
- Ambiguous wrapper folders are rejected rather than selecting one nested package arbitrarily.
- Preparation is staged transactionally and preserves the last working prepared cache until the replacement and registry update both succeed.
- Prepared records store the metadata database fingerprint and preparation time.
- GameBanana downloads use immutable per-submission/per-file locations, temporary partial files, HTTPS redirect validation, JSON/download size limits, and exact archive provenance.
- Remote GameBanana metadata is applied before selecting the immutable source path, keeping the record version and storage version consistent.

### Profiles and future feature boundaries

- Profiles now retain region, installation identity, and per-mod option space.
- Plans block wrong-region mods, wrong-installation profiles, unsupported package backends, stale prepared caches, missing dependencies, declared incompatibilities, invalid manifests, missing mods, and unprepared mods.
- Duplicate profile entries are deduplicated and reported instead of creating self-conflicts.
- Added explicit provider and deployment-backend contracts.
- Hachimi packages remain discoverable and preservable, but are clearly blocked until a separately tested runtime backend exists.
- Added a phased feature roadmap covering multi-install targets, provider-neutral downloads, staged updates, deployment backends, native Studio tools, and the optional runtime bridge.

### GUI and Studio

- Selected GameBanana mods now display their parsed preview image above the description and file selector.
- Preview loading is asynchronous, selection-tokened, session-cached, verified HTTPS-only, limited to 12 MiB and 40 megapixels, and non-blocking when an image is unavailable.
- Pillow raster codecs are included in both frozen package formats so JPEG, PNG, GIF, and WebP previews render consistently.
- Background task callbacks are discarded after GUI shutdown instead of calling a destroyed Tcl interpreter.
- Corrupt settings are quarantined with their original bytes preserved, then reset to defaults with a diagnostics warning.
- Installation detection stores an installation key and prepared-metadata fingerprint; manual path edits deliberately clear verified identity.
- The legacy Studio host watches the game for its full lifetime and closes when Umamusume starts.

## 0.2.0~alpha5 - 2026-07-22

### Fixed

- GameBanana HTTPS now resolves the target system's certificate trust store instead of relying on OpenSSL paths inherited from the Ubuntu build runner.
- Fedora, Bazzite, RHEL, Debian, Ubuntu, Mint, Alpine, SUSE, and common BSD-style CA bundle locations are recognized.
- `SSL_CERT_FILE` and `SSL_CERT_DIR` are honored and validated explicitly.
- A bundled `certifi` Mozilla CA bundle provides a portable fallback when the target system path cannot be resolved.
- GameBanana certificate failures now report the selected trust source and never recommend disabling verification.

### Diagnostics and packaging

- Manager diagnostics now report whether HTTPS certificate verification is ready and which CA file or directory is selected.
- Dedicated TLS tests cover Fedora/Bazzite path fallback, invalid explicit environment paths, SSL context construction, diagnostics, and actionable GameBanana errors.
- The frozen DEB and AppImage are both inspected for the bundled `certifi/cacert.pem` file.
- Complete frozen-runtime parity checks between the source bundle, DEB, and AppImage remain required.

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
