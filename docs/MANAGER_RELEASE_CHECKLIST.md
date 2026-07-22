# UMML Manager release checklist

PR #2 remains draft until these real-machine checks are completed. CI proves that the source, tests, shared frozen runtime, Debian package, and AppImage build reproducibly; it does not prove compatibility with every current game update, desktop, or mod archive.

## Real mod corpus

- [ ] Import and prepare at least one ZIP package and one extracted-folder mod.
- [ ] Import UM:PD Dark Mode through the generic GameBanana provider.
- [ ] Apply two non-conflicting mods and verify exact vanilla restoration.
- [ ] Apply two mods replacing the same hash and verify the load-order winner.
- [ ] Switch between at least three profiles without stale targets.
- [ ] Update one remotely sourced mod and verify version coexistence and rollback.
- [ ] Confirm an enabled unprepared mod blocks apply with a clear explanation.
- [ ] Change an active file outside UMML Manager and confirm normal deployment refuses to overwrite it.
- [ ] Corrupt a copy of `active.json` and confirm deployment fails before changing a game file.
- [ ] Exercise explicit force recovery and record the expected ownership result.

## Platforms and game updates

- [ ] Test game-running detection on native Windows.
- [ ] Test game-running detection under Proton.
- [ ] Test after the game replaces `meta` and `dat` during an update.
- [ ] Verify prepared caches are invalidated or rebuilt when metadata changes.
- [ ] Verify a game update cannot silently replace the stored vanilla baseline.
- [ ] Test a game installation and Proton prefix on different Steam libraries.
- [ ] Test a machine with both Global and Japan installed and add an explicit installation chooser if automatic preference is ambiguous.

## Providers and archives

- [ ] Verify current GameBanana API response fields, file ordering, redirects, and filenames.
- [ ] Confirm switching pages/queries cannot install the previously selected submission.
- [ ] Retain explicit file pinning, source metadata, and archive SHA-256.
- [ ] Add safely inspected 7z/RAR support before advertising broad one-click compatibility for those formats.
- [x] Enforce extracted-file count and declared uncompressed-size limits for ZIP/TAR imports.
- [x] Reject traversal, absolute paths, links, devices, special files, encrypted ZIP entries, and unreasonably long member names.
- [ ] Exercise the archive limits with a large real-world fixture on a constrained disk.
- [ ] Confirm failed downloads and extraction leave no importable partial record.
- [ ] Verify third-party license and attribution metadata remain visible.
- [ ] Add native Hachimi-runtime deployment or clearly keep pure Hachimi packages non-deployable and unprepared.

## Profiles and compatibility

- [ ] Enforce declared Global/Japan/Taiwan region compatibility before profile deployment.
- [ ] Add profile duplicate, rename, and delete actions.
- [ ] Add a visible update action and version-switch workflow in the GUI.
- [ ] Verify older immutable versions remain discoverable and selectable after an update.
- [ ] Add dependency/incompatibility metadata before advertising automatic dependency handling.

## Shared frozen runtime

- [x] Build the manager once with PyInstaller.
- [x] Use the same frozen bundle as the input for both package formats.
- [x] Extract the AppImage in CI and compare its embedded `umml-manager-bin` byte-for-byte with the source frozen bundle.
- [ ] Confirm GUI, CLI, Studio, auto-detection, and GameBanana work identically in both formats on a real desktop.
- [ ] Confirm both formats use the same XDG manager data root without divergent state.

## Debian package

- [x] CI builds `umml-manager_<MANAGER_VERSION>_amd64.deb` successfully.
- [x] Package metadata reports `Package: umml-manager` and the expected version.
- [ ] Install beside `umml-linux` and confirm there are no owned-file conflicts.
- [ ] Launch GUI from the desktop menu without a terminal.
- [ ] Confirm the Debian desktop entry starts `/usr/bin/umml-manager`, not a user PATH shadow.
- [ ] Test migration from the historical alpha1 `~/.local/bin` and per-user desktop entry.
- [ ] Run `umml-manager-cli --version` and an isolated-root `list` command.
- [ ] Confirm the package does not need system `pip` or legacy UMML.
- [ ] Remove `umml-manager` and confirm legacy UMML remains installed and usable.
- [ ] Confirm package removal does not delete user library, profiles, state, or backups.
- [x] Validate desktop and AppStream metadata.

## AppImage package

- [ ] CI builds `umml-manager_<DISPLAY_VERSION>_x86_64.AppImage` successfully.
- [ ] Confirm the AppImage reports the expected manager version.
- [ ] Confirm `--cli --help` and an isolated-root `list` command work without a display server.
- [ ] Launch the AppImage GUI on Linux Mint/Bazzite.
- [ ] Launch on at least one second distribution or container-compatible desktop environment.
- [ ] Open every Studio compatibility tool from the AppImage.
- [ ] Confirm the AppImage can run through extraction mode when FUSE mounting is unavailable.
- [ ] Confirm the AppImage desktop file, icon, and AppStream metadata integrate correctly.
- [ ] Confirm no absolute `/usr/lib/umml-manager` dependency leaks into AppRun or AppDir launchers.

## Checksums and release assets

- [ ] Generate `SHA256SUMS` only after the DEB and AppImage are final.
- [ ] Verify `sha256sum -c SHA256SUMS` in CI.
- [ ] Publish DEB, AppImage, and `SHA256SUMS` together.
- [ ] Do not embed package checksums inside documentation included in those same packages.

## Source installer

- [ ] Install without legacy UMML using a supported Python/Tk environment.
- [ ] Install with legacy UMML and confirm its isolated Python is reused.
- [ ] Confirm source code lives in `~/.local/share/umml-manager-app` while user data remains in `~/.local/share/umml-manager`.
- [ ] Confirm source-specific desktop ID and launchers do not shadow the Debian package.
- [ ] Run the current source uninstaller and confirm it preserves library, profiles, settings, baseline, transactions, downloads, and workspaces.
- [ ] Migrate an historical mixed alpha1 source install without deleting user data.

## Release behavior

- [ ] Keep remote installation opt-in.
- [ ] Preserve previous versions for rollback.
- [ ] Never execute code from downloaded mods.
- [ ] Keep runtime/native plugins outside the desktop manager packages.
- [ ] Attach sanitized logs and state manifests for release-candidate smoke tests.
- [ ] Update `MANAGER_VERSION`, `MANAGER_CHANGELOG.md`, README examples, AppStream metadata, tests, and artifact names together.

## Runtime boundary

- [ ] Do not bundle an injector or Unity hook in either manager package.
- [ ] Unknown game builds expose zero hot-reload features.
- [ ] Queue profile changes for restart rather than writing game files in-process.
- [ ] Keep any future native adapter independently disableable and version-gated.
