# UMML Manager

UMML Manager is the full desktop manager and editing workspace for **Umamusume Pretty Derby** mods. It is packaged separately from legacy UMML, but it deliberately preserves the loader's useful editing tools rather than replacing them with a decorative list of toggles.

> **Preview:** `0.2.0~alpha1`. Profiles, conflict planning, transactional deployment, local discovery, GameBanana browsing, editable workspaces, and the legacy Studio bridge are implemented. Real-game testing is still required before a stable release.

## Install

```bash
sudo apt install ./umml-manager_0.2.0~alpha1_amd64.deb
umml-manager
```

The package can coexist with `umml-linux`. It owns `/usr/lib/umml-manager`, `umml-manager`, and `umml-manager-cli` only.

## Interface

The dark desktop shell is split into focused workspaces:

- **Library:** installed mods, profiles, load order, preparation state, editable copies, and apply actions.
- **Discover:** browse Umamusume mods on GameBanana or scan Downloads and custom folders for compatible packages.
- **Studio:** open every legacy character, dress, training, story, model-swap, translation, cleanup, database, preview, manual-load, and restore tool.
- **Conflicts:** inspect the exact winning provider for every overlapping file before deployment.
- **Settings:** game paths, metadata database, region, diagnostics, manager data, and workspace locations.

## GameBanana browser

The Discover page browses the separate GameBanana listings for:

- Umamusume Pretty Derby Global;
- Umamusume Pretty Derby Japan.

It supports paging, text search, sorting by updated/new/popular/downloads/views, descriptions, authors, versions, statistics, downloadable file selection, opening the original page, direct download, and import into the immutable manager library.

The provider still supports a pasted URL or numeric submission ID through the CLI:

```bash
umml-manager-cli browse --region global --sort popular
umml-manager-cli browse --region japan --query texture
umml-manager-cli gamebanana https://gamebanana.com/mods/123456
```

## Automatic mod detection

The local Discover page scans bounded roots such as Downloads, Documents, Desktop, and user-added folders. It detects:

- `umml-mod.json`;
- `setting.json`;
- `setting.yml` and `setting.yaml`;
- nested folders containing real `assets/` content;
- Hachimi-style folders;
- ZIP and TAR archives containing recognizable mod markers.

The scanner is depth- and entry-limited and skips Steam libraries, Proton prefixes, VCS directories, caches, and dependency trees. Selecting a parent download folder is enough; the importer resolves the real nested mod root.

```bash
umml-manager-cli scan ~/Downloads ~/Mods
umml-manager-cli import ~/Downloads/author-package
```

## Editing without losing features

Imported source versions remain immutable. **Edit copy** creates a timestamped workspace under the manager data directory and writes `.umml-workspace.json` with provenance. Editing that copy cannot mutate the downloaded source version.

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

Mutating legacy actions are guarded and refuse to run while Umamusume is detected. The compatibility host is included in the manager package, so installing the separate legacy DEB is not required for Studio.

## Profiles and deployment

Profiles are ordered lists. Later mods win conflicts. Applying a profile:

1. resolves the complete file plan;
2. validates prepared sources;
3. checks whether the game is running;
4. verifies active files against the previous deployment manifest;
5. captures untouched vanilla files once;
6. stages and commits replacements transactionally;
7. records ownership and hashes for recovery.

An empty profile restores previously managed paths. Files changed by another tool are never overwritten silently.

## First run

1. Launch the game once and complete its download.
2. Close the game.
3. Open **Settings** and select `Persistent/dat`, the game directory, and a decrypted metadata DB.
4. Browse GameBanana or scan local folders from **Discover**.
5. Import and prepare compatible mods.
6. Enable them in a profile and arrange load order.
7. Inspect **Conflicts**.
8. Apply the profile.

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

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-build.txt
bash scripts/check_manager.sh
bash scripts/build_manager_frozen.sh
bash scripts/build_manager_deb.sh
```

Read `CONTRIBUTING.md`, `docs/MANAGER_ARCHITECTURE.md`, `docs/MANAGER_DEVELOPMENT.md`, and `docs/PACKAGING.md` before changing state, deployment, providers, archives, or packaging.

## Safety

- Keep the game closed during apply, restore, database editing, and other mutating Studio operations.
- Imported archives and provider responses are untrusted input.
- Do not commit game files, decrypted metadata, downloaded archives, manager state, or user paths.
- Modding may violate the game's terms of service.

UMML Manager code is MIT-licensed. Imported mods retain their own licenses.
