# UMML Manager

UMML Manager is the full desktop manager and editing workspace for **Umamusume Pretty Derby** mods. It is packaged separately from legacy UMML, but it deliberately preserves the loader's useful editing tools rather than replacing them with a decorative list of toggles.

> **Preview:** `0.2.0~alpha4`. Profiles, conflict planning, transactional deployment, automatic installation detection, local discovery, GameBanana browsing, editable workspaces, the legacy Studio bridge, and separate DEB/AppImage packaging are implemented. Real-game testing is still required before a stable release.

## Install

### Debian package

```bash
sudo apt install ./umml-manager_0.2.0~alpha4_amd64.deb
/usr/bin/umml-manager
```

The package can coexist with `umml-linux`. It owns `/usr/lib/umml-manager`, `/usr/bin/umml-manager`, and `/usr/bin/umml-manager-cli` only.

The Debian desktop file launches `/usr/bin/umml-manager` directly. This avoids an older source-installed `~/.local/bin/umml-manager` shadowing the package.

### AppImage

```bash
chmod +x ./umml-manager_0.2.0-alpha4_x86_64.AppImage
./umml-manager_0.2.0-alpha4_x86_64.AppImage
```

The AppImage supports the same CLI without installing files into `/usr`:

```bash
./umml-manager_0.2.0-alpha4_x86_64.AppImage --version
./umml-manager_0.2.0-alpha4_x86_64.AppImage --cli list
./umml-manager_0.2.0-alpha4_x86_64.AppImage --cli browse --region global
```

The DEB and AppImage are built from the same PyInstaller bundle. CI extracts the AppImage and compares its embedded `umml-manager-bin` byte-for-byte with the frozen bundle used to build the DEB.

Both formats use the same user data directory:

```text
~/.local/share/umml-manager
```

Changing package format does not create a second library or alter profiles. Download the external `umml-manager-checksums` workflow artifact and verify either package with:

```bash
sha256sum -c SHA256SUMS
```

### Historical source-install cleanup

Early manager previews installed application code into the same directory as manager data. **Do not use an old alpha1 `uninstall-manager.sh`**, because it could delete the mixed directory.

To remove only the stale alpha1 launchers while preserving the library and profiles:

```bash
rm -f ~/.local/bin/umml-manager ~/.local/bin/umml-manager-cli
rm -f ~/.local/share/applications/io.github.evelynlimab.ummlmanager.desktop
update-desktop-database ~/.local/share/applications 2>/dev/null || true
hash -r
```

The current source installer stores application files in `~/.local/share/umml-manager-app` and keeps user data in `~/.local/share/umml-manager`. It creates `umml-manager-source` and `umml-manager-source-cli`; generic compatibility commands prefer the Debian package when installed.

## Interface

The dark desktop shell is split into focused workspaces:

- **Library:** installed mods, profiles, load order, preparation state, editable copies, and apply actions.
- **Discover:** browse Umamusume mods on GameBanana or scan Downloads and custom folders for compatible packages.
- **Studio:** open every legacy character, dress, training, story, model-swap, translation, cleanup, database, preview, manual-load, and restore tool.
- **Conflicts:** inspect the exact winning provider for every overlapping file before deployment.
- **Settings:** automatic installation setup, game paths, metadata database, region, diagnostics, manager data, and workspace locations.

## First run

1. Launch the game once and complete its download.
2. Open UMML Manager. Detection may run while the game is open, but deployment cannot.
3. The manager detects Steam/Proton and prepares a readable `meta_decrypted_*.db` automatically.
4. If detection does not complete, use **Settings → Auto-detect installation**, then **Run diagnostics**.
5. Browse GameBanana or scan local folders from **Discover**.
6. Import and prepare compatible mods.
7. Enable them in a profile and arrange load order.
8. Close the game, inspect **Conflicts**, and apply the profile.

Manual path selection is retained for unusual layouts. The three paths are:

- game asset data: `.../Persistent/dat`;
- prepared metadata: UMML's `meta_decrypted_*.db`, not the encrypted game file named `meta`;
- game installation directory: the Steam/DMM directory containing the executable.

## GameBanana browser

The Discover page browses the separate GameBanana listings for:

- Umamusume Pretty Derby Global;
- Umamusume Pretty Derby Japan.

It supports paging, text search, sorting by updated/new/popular/downloads/views, descriptions, authors, versions, statistics, downloadable file selection, opening the original page, direct download, and import into the manager library. Changing pages clears the previous selection so an old result cannot be installed accidentally.

```bash
umml-manager-cli browse --region global --sort popular
umml-manager-cli browse --region japan --query texture
umml-manager-cli gamebanana https://gamebanana.com/mods/123456
```

For AppImage CLI usage, prefix those commands with the AppImage filename and `--cli`.

## Automatic mod detection

The local Discover page scans bounded roots such as Downloads, Documents, Desktop, and user-added folders. It detects:

- `umml-mod.json`;
- `setting.json`;
- `setting.yml` and `setting.yaml`;
- nested folders containing real `assets/` content;
- Hachimi-style folders;
- ZIP and TAR archives containing recognizable mod markers.

The scanner is depth- and entry-limited and skips Steam libraries, Proton prefixes, VCS directories, caches, and dependency trees. Selecting a parent download folder is enough; the importer resolves the real nested mod root.

Archive extraction is independently constrained before any files are written:

- maximum 20,000 entries;
- maximum 8 GiB declared expanded size;
- traversal and absolute paths rejected;
- links, devices, FIFOs, and ZIP special files rejected;
- encrypted ZIP entries rejected;
- unusually long member names rejected.

A pure Hachimi package may be discovered and preserved in the library, but the current transactional hash-asset deployer does not install Hachimi runtime layouts. It remains **unprepared** and therefore blocks profile application instead of silently pretending to work.

```bash
umml-manager-cli scan ~/Downloads ~/Mods
umml-manager-cli import ~/Downloads/author-package
```

## Editing without losing features

Imported source versions remain immutable. Re-importing the same ID and version with different contents is rejected. A different version receives a distinct manager record so the registered previous version is not replaced.

**Edit copy** creates a timestamped workspace under the manager data directory and writes `.umml-workspace.json` with provenance. Change the edited package's version or import ID before importing it as a new immutable local mod.

The Studio compatibility host exposes the complete legacy loader interface plus direct launch cards for:

- character attributes;
- personality;
- dresses;
- training;
- story and concert editing;
- body/head/tail/chibi character swaps;
- translation merge;
- unused-asset cleanup;
- master database reset;
- regular asset preview, manual loading, restoration, and the rest of the legacy workspace.

Mutating legacy actions are guarded and refuse to run while Umamusume is detected. The compatibility host is included in both manager package formats, so installing the separate legacy DEB is not required for Studio.

## Profiles and deployment

Profiles are ordered lists. Later mods win conflicts. Applying a profile:

1. resolves the complete file plan;
2. rejects missing or unprepared enabled mods;
3. checks whether the game is running;
4. validates the previous deployment state instead of treating corruption as empty state;
5. verifies active files against the previous deployment manifest;
6. captures untouched vanilla files once;
7. stages and commits replacements transactionally;
8. records ownership and hashes for recovery.

An empty profile restores previously managed paths. Files changed by another tool are never overwritten silently.

## CLI

```bash
umml-manager-cli list
umml-manager-cli scan ~/Downloads
umml-manager-cli browse --region global --sort updated
umml-manager-cli workspace creator.mod
umml-manager-cli studio attributes --dat /path/to/Persistent/dat
umml-manager-cli prepare creator.mod --meta /path/to/meta_decrypted.db
umml-manager-cli profile Default creator.mod another.mod
umml-manager-cli plan Default
umml-manager-cli apply Default --dat /path/to/Persistent/dat --game-dir /path/to/game
```

AppImage equivalent:

```bash
./umml-manager_0.2.0-alpha4_x86_64.AppImage --cli list
./umml-manager_0.2.0-alpha4_x86_64.AppImage --cli plan Default
```

## Development and packaging

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-build.txt
bash scripts/check_manager.sh
bash scripts/build_manager_frozen.sh
bash scripts/build_manager_deb.sh
bash scripts/build_manager_appimage.sh
```

`build_manager_appimage.sh` downloads the official `AppImage/appimagetool` continuous release asset over HTTPS and verifies it against GitHub's published SHA-256 digest before running it. Replacement of that asset therefore fails CI until the new binary is reviewed and its pin is deliberately updated.

Read `CONTRIBUTING.md`, `docs/MANAGER_ARCHITECTURE.md`, `docs/MANAGER_DEVELOPMENT.md`, and `docs/PACKAGING.md` before changing state, deployment, providers, archives, or packaging.

## Safety

- Keep the game closed during apply, restore, database editing, and other mutating Studio operations.
- Imported archives and provider responses are untrusted input.
- Do not commit game files, decrypted metadata, downloaded archives, manager state, or user paths.
- Modding may violate the game's terms of service.

UMML Manager code is MIT-licensed. Imported mods retain their own licenses.
