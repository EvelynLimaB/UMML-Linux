# UMML Manager

UMML Manager is the full desktop manager and editing workspace for **Umamusume Pretty Derby** mods. It is packaged separately from legacy UMML, but preserves the loader's useful editing tools instead of replacing them with a decorative list of toggles.

> **Preview:** `0.2.0~alpha6`. The manager has undergone a full module-by-module code audit covering persistent state, local and remote imports, preparation, profile planning, deployment, recovery, installation detection, Studio isolation, GUI threading, and both Linux package formats. Real-game and destructive recovery testing remain required before a stable release.

## Install

### Debian package

```bash
sudo apt install ./umml-manager_0.2.0~alpha6_amd64.deb
/usr/bin/umml-manager
```

The package can coexist with `umml-linux`. It owns `/usr/lib/umml-manager`, `/usr/bin/umml-manager`, and `/usr/bin/umml-manager-cli` only.

### AppImage

```bash
chmod +x ./umml-manager_0.2.0-alpha6_x86_64.AppImage
./umml-manager_0.2.0-alpha6_x86_64.AppImage
```

The same file exposes the CLI:

```bash
./umml-manager_0.2.0-alpha6_x86_64.AppImage --version
./umml-manager_0.2.0-alpha6_x86_64.AppImage --cli list
./umml-manager_0.2.0-alpha6_x86_64.AppImage --cli browse --region global
```

The DEB and AppImage are built from one PyInstaller bundle. CI extracts both finished packages and compares their complete frozen runtime trees with the source bundle and each other.

Both formats use:

```text
~/.local/share/umml-manager
```

Changing package format does not create another library or migrate profiles. Verify downloads with the separate `SHA256SUMS` artifact:

```bash
sha256sum -c SHA256SUMS
```

### Historical source-install cleanup

Early previews installed application code into the same directory as manager data. **Do not use an old alpha1 `uninstall-manager.sh`**, because it could delete that mixed directory.

Remove only stale alpha1 launchers while preserving the library and recovery state:

```bash
rm -f ~/.local/bin/umml-manager ~/.local/bin/umml-manager-cli
rm -f ~/.local/share/applications/io.github.evelynlimab.ummlmanager.desktop
update-desktop-database ~/.local/share/applications 2>/dev/null || true
hash -r
```

The current source installer stores code in `~/.local/share/umml-manager-app` and user state in `~/.local/share/umml-manager`. It creates `umml-manager-source` and `umml-manager-source-cli`; generic compatibility launchers prefer the Debian package when installed.

## Interface

- **Library:** immutable installed versions, profiles, load order, preparation state, stale-cache status, editable copies, and deployment.
- **Discover:** browse Umamusume GameBanana or scan bounded local roots for recognizable packages.
- **Studio:** launch the legacy character, dress, training, story, model-swap, translation, cleanup, database, preview, manual-load, and restore tools.
- **Conflicts:** inspect the exact winning provider and every deployment blocker.
- **Settings:** installation detection, game paths, prepared metadata, region, diagnostics, manager data, and workspace locations.

## First run

1. Launch the game once and complete its data download.
2. Open UMML Manager. Detection may run while the game is open; deployment may not.
3. The manager detects Steam/Proton or DMM, validates the installation paths, prepares `meta_decrypted_*.db`, records an installation key, and fingerprints the prepared metadata.
4. When detection does not complete, use **Settings → Auto-detect installation**, then **Run diagnostics**.
5. Browse GameBanana or scan local folders from **Discover**.
6. Import and prepare compatible packages.
7. Enable them in a profile and arrange load order.
8. Inspect **Conflicts**. The plan must have zero blockers.
9. Close the game and apply the profile.

Manual path selection remains available for unusual layouts. Manual changes deliberately clear the verified installation key and metadata fingerprint until detection is run again.

The three paths are:

- `.../Persistent/dat` for game asset files;
- UMML's prepared `meta_decrypted_*.db`, not the encrypted file named `meta`;
- the game installation directory containing its executable.

## HTTPS and GameBanana

UMML resolves certificate trust in this order:

1. validated `SSL_CERT_FILE` and `SSL_CERT_DIR` values;
2. usable target-system OpenSSL defaults;
3. known Fedora/Bazzite, RHEL, Debian, Ubuntu, Mint, Alpine, SUSE, and BSD-style CA locations;
4. the bundled `certifi` Mozilla CA bundle.

Certificate verification is never disabled. **Run diagnostics** reports the selected trust source and CA path. Explicit but invalid CA configuration fails closed instead of silently changing trust stores.

Discover browses the separate GameBanana listings for Global and Japan. It supports paging, search, sorting, descriptions, authors, versions, statistics, downloadable-file selection, opening the original page, verified download, and direct import.

Downloads are written to temporary partial files under immutable per-submission/per-file locations. Final redirects must remain HTTPS; response and download sizes are bounded; SHA-256, filename, byte size, file ID, submission ID, and fetch time are retained as provenance.

```bash
umml-manager-cli browse --region global --sort popular
umml-manager-cli browse --region japan --query texture
umml-manager-cli gamebanana https://gamebanana.com/mods/123456
```

## Automatic mod discovery and imports

The scanner uses Downloads, Documents, Desktop, XDG user directories, and user-added roots. It is depth- and entry-limited and skips Steam libraries, Proton prefixes, VCS directories, caches, dependencies, hidden directories, and symbolic links.

Automatic detection requires recognizable evidence. An ordinary `setting.json` or unrelated ZIP is not listed as a mod merely because it exists. A mod-like archive with an unknown layout may appear as **low confidence** for manual verification.

Recognized content includes:

- `umml-mod.json`;
- valid UMML metadata combined with real `assets/` content;
- populated legacy `assets/` layouts;
- populated Hachimi layouts;
- ZIP and TAR archives containing those markers.

Archive and local-folder imports reject traversal, absolute paths, drive prefixes, symlinks, devices, FIFOs, sockets, duplicate archive paths, encrypted ZIP entries, extremely long names, more than 20,000 archive entries, and more than 8 GiB declared or actual extraction.

Local folder copies are revalidated and hashed after copying. When the source changes during import, nothing is registered or committed as an immutable version.

Ambiguous wrapper folders containing multiple nearest mod roots are rejected instead of selecting one arbitrarily.

A Hachimi package may be detected and preserved, but the current backend cannot deploy it. Detection is not treated as support; profiles containing it remain blocked.

```bash
umml-manager-cli scan ~/Downloads ~/Mods
umml-manager-cli import ~/Downloads/author-package
```

## Immutable versions and editable workspaces

Imported source versions are immutable. Re-importing the same ID and version with different contents is rejected. Different versions coexist under separate records and safe storage components; arbitrary display version text cannot escape the manager data root.

**Edit copy** creates a timestamped workspace with `.umml-workspace.json`, the base mod ID/version, and the original source-tree digest. Change the edited package's ID or version before importing it as a new immutable version.

## Preparation and stale caches

Legacy hashed assets are decoded into a staging directory. The previous prepared cache is not removed until the replacement is complete, non-empty, duplicate-free, and successfully registered.

Prepared records store:

- the prepared-file manifest and SHA-256 values;
- the SHA-256 of the metadata database used for preparation;
- the preparation time.

When the current metadata fingerprint changes after a game update, the plan marks the cache **stale** and blocks deployment until it is re-prepared.

## Profiles and conflict planning

Profiles are ordered lists; later mods win overlapping file paths. Profiles also retain target region, installation identity, and space for future per-mod options.

The plan blocks deployment for:

- missing or unprepared mods;
- stale prepared caches;
- unsupported package backends;
- wrong-region mods;
- a profile bound to another installation;
- invalid paths or hashes;
- missing declared dependencies;
- declared incompatibilities.

Duplicate profile entries are removed and reported rather than creating self-conflicts.

## Verified transactional deployment

Before game-file mutation, the engine:

1. validates the complete plan;
2. verifies the target installation identity and vanilla-baseline scope;
3. acquires a cross-process target lock;
4. recovers or finalizes earlier interrupted transactions;
5. verifies every prepared source file against its manifest SHA-256;
6. confirms the game is closed;
7. snapshots every affected target and records snapshot hashes in a durable journal.

During deployment it uses contained paths and atomic replacement, verifies installed files after copying, captures untouched vanilla files once, stores independent baseline integrity records, and writes target-scoped active ownership state.

An empty profile restores managed paths from verified baselines. Active files changed by another tool are not overwritten unless force recovery is explicitly requested from the CLI.

Unreadable, future-version, wrong-target, malformed, or tampered critical state fails closed. Corrupt preferences are different: their raw bytes are quarantined and defaults are loaded, because losing a window preference is not the same class of event as guessing at deployment ownership.

## Legacy Studio

The compatibility host includes the full legacy loader interface and direct tool launch cards. Mutating legacy entry points check for the game process. The host also watches for Umamusume during its entire lifetime and closes when the game starts, reducing the risk from nested legacy editor callbacks.

Native Studio pages will replace these editors incrementally. The compatibility host remains until each feature has a tested equivalent and restoration coverage.

## CLI

```bash
umml-manager-cli list
umml-manager-cli scan ~/Downloads
umml-manager-cli browse --region global --sort updated
umml-manager-cli workspace creator.mod
umml-manager-cli studio attributes --dat /path/to/Persistent/dat
umml-manager-cli prepare creator.mod --meta /path/to/meta_decrypted.db
umml-manager-cli profile Default creator.mod another.mod \
  --region global --installation-key steam-global
umml-manager-cli plan Default \
  --region global --installation-key steam-global \
  --meta /path/to/meta_decrypted.db
umml-manager-cli apply Default \
  --dat /path/to/Persistent/dat \
  --game-dir /path/to/game \
  --region global --installation-key steam-global \
  --meta /path/to/meta_decrypted.db
```

For AppImage use, prefix the CLI arguments with the AppImage filename and `--cli`.

## Development and packaging

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-build.txt
python scripts/audit_manager.py
bash scripts/check_manager.sh
bash scripts/build_manager_frozen.sh
bash scripts/build_manager_deb.sh
bash scripts/build_manager_appimage.sh
```

The structural audit uses only the Python standard library and guards dangerous calls and core architecture boundaries. Regression tests include adversarial paths, archive extraction, local symlinks, immutable sources, provider failures, stale metadata, cross-install state, tampered baselines, tampered recovery snapshots, schema evolution, and injected disk/copy failures.

Read:

- `CONTRIBUTING.md` for contribution rules;
- `docs/MANAGER_ARCHITECTURE.md` for boundaries;
- `docs/MANAGER_DEVELOPMENT.md` for workflows;
- `docs/MANAGER_AUDIT.md` for the detailed findings;
- `docs/MANAGER_FEATURE_ROADMAP.md` for the ordered feature plan;
- `docs/PACKAGING.md` for package reproducibility.

## Remaining alpha release gates

- live Bazzite GameBanana browse and download without certificate overrides;
- a broader real-mod corpus;
- packaged apply/disable/restore/update tests on disposable game data;
- deliberate process-kill recovery drills at several transaction points;
- explicit multi-installation target UI and separately scoped state directories;
- native Hachimi deployment;
- native Studio service extraction and generated local mods;
- exact-build runtime/in-game integration as a separate optional component.

## Safety

- Keep the game closed during apply, restore, database editing, and other mutating Studio operations.
- Treat archives, provider responses, manifests, manager state, and recovery material as untrusted input.
- Do not delete interrupted transaction directories until diagnostics or recovery has explained them.
- Do not commit game files, decrypted metadata, downloaded archives, manager state, or user paths.
- Modding may violate the game's terms of service.

UMML Manager code is MIT-licensed. Imported mods retain their own licenses.
