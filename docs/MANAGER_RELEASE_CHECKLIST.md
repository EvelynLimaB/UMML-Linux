# UMML Manager release checklist

PR #2 remains draft until these real-machine checks are completed. CI proves that
the source, tests, frozen runtime, and Debian package build reproducibly; it does
not prove compatibility with every current game update or mod archive.

## Real mod corpus

- [ ] Import and prepare at least one ZIP package and one extracted-folder mod.
- [ ] Import UM:PD Dark Mode through the generic GameBanana provider.
- [ ] Apply two non-conflicting mods and verify exact vanilla restoration.
- [ ] Apply two mods replacing the same hash and verify the load-order winner.
- [ ] Switch between at least three profiles without stale targets.
- [ ] Update one remotely sourced mod and verify version coexistence and rollback.
- [ ] Change an active file outside UMML Manager and confirm normal deployment
      refuses to overwrite it.
- [ ] Exercise explicit force recovery and record the expected ownership result.

## Platforms and game updates

- [ ] Test game-running detection on native Windows.
- [ ] Test game-running detection under Proton.
- [ ] Test after the game replaces `meta` and `dat` during an update.
- [ ] Verify prepared caches are invalidated or rebuilt when metadata changes.
- [ ] Verify a game update cannot silently replace the stored vanilla baseline.
- [ ] Test a game installation and Proton prefix on different Steam libraries.

## Providers and archives

- [ ] Verify current GameBanana API response fields, file ordering, redirects, and
      filenames.
- [ ] Retain explicit file pinning, source metadata, and archive SHA-256.
- [ ] Add safely inspected 7z/RAR support before advertising broad one-click
      compatibility for those formats.
- [ ] Add extracted-file count and uncompressed-size limits before importing
      untrusted large archives.
- [ ] Confirm failed downloads and extraction leave no importable partial record.
- [ ] Verify third-party license and attribution metadata remain visible.

## Separate Debian package

- [ ] CI builds `umml-manager_<MANAGER_VERSION>_amd64.deb` successfully.
- [ ] Package metadata reports `Package: umml-manager` and the expected version.
- [ ] Install beside `umml-linux` and confirm there are no owned-file conflicts.
- [ ] Launch GUI from the desktop menu without a terminal.
- [ ] Run `umml-manager-cli --version` and an isolated-root `list` command.
- [ ] Confirm the package does not need system `pip` or legacy UMML.
- [ ] Remove `umml-manager` and confirm legacy UMML remains installed and usable.
- [ ] Confirm package removal does not delete user library, profiles, state, or
      backups.
- [ ] Validate desktop and AppStream metadata.
- [ ] Generate and publish SHA-256 checksums for the release artifact.

## Source installer

- [ ] Install without legacy UMML using a supported Python/Tk environment.
- [ ] Install with legacy UMML and confirm its isolated Python is reused.
- [ ] Confirm the source installer installs the distinct manager icon and desktop
      ID.
- [ ] Confirm the source uninstaller removes application files but not game files
      or XDG state/cache data.

## Release behavior

- [ ] Keep remote installation opt-in.
- [ ] Preserve previous versions for rollback.
- [ ] Never execute code from downloaded mods.
- [ ] Keep runtime/native plugins outside the desktop manager.
- [ ] Attach sanitized logs and state manifests for release-candidate smoke tests.
- [ ] Update `MANAGER_VERSION`, `MANAGER_CHANGELOG.md`, README examples, AppStream
      metadata, and artifact names together.

## Runtime boundary

- [ ] Do not bundle an injector or Unity hook in the manager DEB.
- [ ] Unknown game builds expose zero hot-reload features.
- [ ] Queue profile changes for restart rather than writing game files in-process.
- [ ] Keep any future native adapter independently disableable and version-gated.
