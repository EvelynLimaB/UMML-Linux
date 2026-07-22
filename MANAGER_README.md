# UMML Manager

UMML Manager is the full desktop manager and editing workspace for **Umamusume Pretty Derby** mods. It is packaged separately from legacy UMML, but preserves the loader's editing tools instead of replacing them with a polished list that cannot actually do anything.

> **Preview:** `0.2.0~alpha9`. The manager includes audited persistent state, bounded imports, provider browsing, automatic preparation of compatible imports, profile planning, verified deployment, recovery journals, automatic installation detection, legacy Studio compatibility, and matching DEB/AppImage packages. Real-game and destructive recovery testing remain required before a stable release.

## Install

### Debian package

```bash
sudo apt install ./umml-manager_0.2.0~alpha9_amd64.deb
/usr/bin/umml-manager
```

The package can coexist with `umml-linux`. It owns `/usr/lib/umml-manager`, `/usr/bin/umml-manager`, and `/usr/bin/umml-manager-cli` only.

### AppImage

```bash
chmod +x ./umml-manager_0.2.0-alpha9_x86_64.AppImage
./umml-manager_0.2.0-alpha9_x86_64.AppImage
```

The same file exposes the CLI:

```bash
./umml-manager_0.2.0-alpha9_x86_64.AppImage --version
./umml-manager_0.2.0-alpha9_x86_64.AppImage --cli list
./umml-manager_0.2.0-alpha9_x86_64.AppImage --cli browse --region global
```

The DEB and AppImage are built from one PyInstaller bundle. CI extracts both finished packages and compares their complete frozen runtime trees with the source bundle and each other.

Both formats use:

```text
~/.local/share/umml-manager
```

Changing package format does not create another library. Verify downloads with the separate `SHA256SUMS` artifact:

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
- **Discover:** browse Global/Japan GameBanana or scan bounded local roots for recognizable packages.
- **Studio:** launch the legacy character, dress, training, story, model-swap, translation, cleanup, database, preview, manual-load, and restore tools.
- **Conflicts:** inspect exact file winners and every deployment blocker.
- **Settings:** installation detection, game paths, prepared metadata, region, diagnostics, manager data, and workspaces.

## First run

1. Launch the game once and complete its data download.
2. Open UMML Manager. Detection may run while the game is open; deployment may not.
3. The manager detects Steam/Proton or DMM, validates paths, prepares `meta_decrypted_*.db`, records an installation key, and fingerprints the metadata.
4. When detection does not complete, use **Settings → Auto-detect installation**, then **Run diagnostics**.
5. Browse GameBanana or scan local folders from **Discover**.
6. Import a compatible package. Legacy UMML assets are prepared automatically when readable metadata is available.
7. Enable prepared mods in a profile and arrange load order.
8. Inspect **Conflicts**. The plan must have zero blockers.
9. Close the game and apply the profile explicitly.

Manual path selection remains available for unusual layouts. Manual changes deliberately clear the verified installation key and metadata fingerprint until detection runs again.

The three paths are:

- `.../Persistent/dat` for game asset files;
- UMML's prepared `meta_decrypted_*.db`, not the encrypted file named `meta`;
- the game installation directory containing its executable.

## Import, preparation, and deployment are separate stages

The manager deliberately separates three operations:

1. **Import** preserves an immutable copy of the downloaded or selected source package.
2. **Prepare** converts compatible source assets into verified game-hash targets. Alpha9 performs this automatically after import when the package and metadata are compatible.
3. **Apply** writes an enabled profile to the game. This remains a separate explicit action and requires the game to be closed.

If automatic preparation fails, the imported source is not deleted. It stays in Library with **needs prepare**, and the existing manual preparation action becomes a retry and diagnostic tool rather than required routine work.

Prepared records store the file manifest, SHA-256 values, metadata fingerprint, and preparation time. A changed game metadata fingerprint marks the cache stale and blocks deployment until it is prepared again.

## HTTPS, GameBanana, and preview images

UMML resolves certificate trust in this order:

1. validated `SSL_CERT_FILE` and `SSL_CERT_DIR` values;
2. usable target-system OpenSSL defaults;
3. known Fedora/Bazzite, RHEL, Debian, Ubuntu, Mint, Alpine, SUSE, and BSD-style CA locations;
4. the bundled `certifi` Mozilla CA bundle.

Certificate verification is never disabled. **Run diagnostics** reports the selected trust source and CA path.

Discover supports paging, search, sorting, descriptions, authors, versions, statistics, downloadable-file selection, original-page links, verified download, direct import, and selected-mod preview images.

Catalogue rows do not always include their complete file list. When that happens, the manager immediately offers **Install latest**, fetches the full submission details in a separate background task, and replaces the fallback with the real file selector when available. A failed prefetch does not permanently disable installation; clicking **Install latest** retries the detail request.

GameBanana file containers are normalized from array, mapping, and nested response shapes before they reach the selector. Stale detail responses are ignored after changing selection or page.

Some older GameBanana uploads contain the loose files accepted by the legacy UMML manual loader but omit a modern `assets/` wrapper or manifest. Alpha9 normalizes this layout only when all of the following are true:

- the archive came through the verified GameBanana provider path;
- it contains recognizable UnityFS, audio, video, bundle, or hashed asset evidence;
- it contains no executable, script, or native-library payloads.

Plain documents and unrelated archives remain rejected. The normalized package is stored immutably before automatic preparation begins.

Preview images:

- are normalized through the preview-aware registered GameBanana provider;
- accept only GameBanana-owned HTTPS URLs and redirects;
- load off the UI path with stale-selection protection;
- use a bounded 24-image session cache;
- are limited to 12 MiB and 40 megapixels;
- fail nonfatally so mod details and installation remain usable.

Downloads use temporary partial files under immutable per-submission/per-file locations. Final redirects must remain HTTPS; response and download sizes are bounded; SHA-256, filename, byte size, file ID, submission ID, and fetch time are retained.

```bash
umml-manager-cli browse --region global --sort popular
umml-manager-cli browse --region japan --query texture
umml-manager-cli gamebanana https://gamebanana.com/mods/123456
```

## Automatic mod discovery and imports

The scanner uses Downloads, Documents, Desktop, XDG user directories, and user-added roots. It is depth- and entry-limited and skips Steam libraries, Proton prefixes, VCS directories, caches, dependencies, hidden directories, and symbolic links.

Automatic detection requires recognizable evidence. An ordinary `setting.json` or unrelated ZIP is not listed merely because it exists.

Recognized content includes:

- `umml-mod.json`;
- valid UMML metadata combined with real `assets/` content;
- populated legacy `assets/` layouts;
- populated Hachimi layouts;
- ZIP and TAR archives containing those markers.

Imports reject traversal, absolute paths, drive prefixes, symlinks, devices, FIFOs, sockets, duplicate archive paths, encrypted ZIP entries, extremely long names, more than 20,000 entries, and more than 8 GiB declared or actual extraction.

Local folder copies are revalidated and hashed after copying. Ambiguous wrappers containing multiple nearest mod roots are rejected.

A Hachimi package may be detected and preserved, but the current backend cannot deploy it. Detection is not treated as support; profiles containing it remain blocked.

## Immutable versions and workspaces

Imported source versions are immutable. Re-importing the same ID and version with different contents is rejected. Different versions coexist under safe storage components.

**Edit copy** creates a timestamped workspace with provenance. Change the edited package's ID or version before importing it as a new immutable version.

Legacy hashed assets are decoded into staging. The previous prepared cache remains until the replacement is complete, non-empty, duplicate-free, hashed, and registered.

## Profiles and conflict planning

Profiles are ordered lists; later mods win overlapping paths. Profiles retain target region, installation identity, and future per-mod option space.

The plan blocks deployment for:

- missing or unprepared mods;
- stale prepared caches;
- unsupported backends;
- wrong-region mods;
- a profile bound to another installation;
- invalid paths or hashes;
- missing declared dependencies;
- declared incompatibilities.

Duplicate profile entries are removed and reported rather than creating self-conflicts.

## Verified transactional deployment

Before mutation, the engine validates the plan, verifies target identity, acquires a cross-process lock, recovers earlier transactions, verifies prepared sources, confirms the game is closed, and snapshots every affected target with integrity records.

During deployment it uses contained paths and atomic replacement, verifies installed files, captures untouched vanilla files once, stores baseline integrity records, and writes target-scoped active ownership state.

An empty profile restores managed paths from verified baselines. Active files changed by another tool are not overwritten unless force recovery is explicitly requested from the CLI.

Unreadable, future-version, wrong-target, malformed, or tampered critical state fails closed. Corrupt preferences are quarantined and reset because losing a preference is not the same class of event as guessing deployment ownership.

## Legacy Studio

The compatibility host includes the complete legacy loader interface and direct launch cards. Mutating entry points check the game process, and the host watches for Umamusume throughout its lifetime.

Native Studio pages will replace these editors incrementally. The compatibility host remains until every feature has a tested equivalent and restoration coverage.

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

For AppImage use, prefix CLI arguments with the AppImage filename and `--cli`.

## Development and packaging

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-build.txt
python -m pip check
python scripts/audit_manager.py
bash scripts/check_manager.sh
bash scripts/build_manager_frozen.sh
bash scripts/build_manager_deb.sh
bash scripts/build_manager_appimage.sh
```

CI installs the complete pinned runtime dependency set before manager regressions. Package inspection verifies matching frozen runtime trees, certifi trust data, and Pillow's compiled imaging extension in both formats.

Read `CONTRIBUTING.md`, `docs/MANAGER_ARCHITECTURE.md`, `docs/MANAGER_DEVELOPMENT.md`, `docs/MANAGER_AUDIT.md`, `docs/MANAGER_FEATURE_ROADMAP.md`, and `docs/PACKAGING.md` before changing state, providers, deployment, recovery, or packaging.

## Remaining alpha release gates

- live Bazzite GameBanana browse, preview, detail hydration, loose-package normalization, automatic preparation, and import without certificate overrides;
- visual preview sizing and rapid-selection testing on KDE;
- a broader real-mod corpus;
- packaged apply/disable/restore/update tests on disposable game data;
- deliberate process-kill recovery drills at transaction boundaries;
- explicit multi-installation target UI and separately scoped state directories;
- native Hachimi deployment;
- native Studio service extraction and generated local mods;
- exact-build runtime/in-game integration as a separate optional component.

## Safety

- Keep the game closed during apply, restore, database editing, and other mutating Studio operations.
- Treat archives, provider responses, manifests, manager state, and recovery material as untrusted input.
- Do not delete interrupted transaction directories until diagnostics or recovery explains them.
- Do not commit game files, decrypted metadata, downloaded archives, manager state, or user paths.
- Modding may violate the game's terms of service.

UMML Manager code is MIT-licensed. Imported mods retain their own licenses.
