# UMML Manager architecture

UMML Manager is intentionally separate from the legacy one-folder loader. The
legacy application performs direct, imperative mod operations; the manager owns
a persistent library and computes a complete desired game state from profiles.

## Component boundary

```text
Provider / local import
        │
        ▼
Immutable source library
        │
        ▼
Preparation cache ────── decrypted metadata DB
        │
        ▼
Ordered profile
        │
        ▼
Deterministic resolver
        │
        ├── missing mods/files
        ├── conflict provenance
        └── winning target map
        │
        ▼
Transactional apply engine
        │
        ├── game-running guard
        ├── previous deployment verification
        ├── one-time vanilla baseline
        ├── staging and commit
        └── deployment manifest
        │
        ▼
Game Persistent/dat
```

## Library

The library preserves imported source packages under immutable mod ID/version
paths. An imported record contains descriptive metadata, provider provenance,
source location, preparation state, and a target-file manifest when prepared.

Updating a mod must not replace the bytes representing an already imported
version. The store may select a newer version for a profile, but rollback and
auditing require older records to remain reproducible until the user removes
them intentionally.

## Preparation

Legacy mods provide named files under `assets/`. The preparation adapter uses the
decrypted metadata database to resolve game hashes and encryption keys, producing
a hash-addressed prepared tree.

Preparation is cache construction, not installation. It may run while the game is
open and must never write to `Persistent/dat`.

## Profiles

A profile is an ordered list of stable mod IDs. Profiles do not contain imperative
install/uninstall instructions.

```json
{
  "name": "Dark UI",
  "enabled": [
    "creator.interface-base",
    "creator.dark-mode",
    "creator.icon-override"
  ]
}
```

Later entries have higher priority for overlapping target paths.

## Resolver

The resolver is a pure planning stage. Given the same profile and library records,
it must produce the same result regardless of filesystem enumeration order,
network availability, locale, or current time.

A resolution contains:

- enabled mod order;
- missing mod IDs;
- missing prepared assets;
- one winner for each target path;
- every overridden provider for conflicted paths;
- provenance sufficient for GUI and CLI explanations.

The resolver does not touch the game directory.

## Apply engine

The apply engine receives a complete resolution and transforms the current managed
state into that desired state.

Before writing, it verifies:

- the game is not running;
- prepared sources still match their recorded hashes;
- target paths are safe and relative;
- active managed files still match the previous deployment manifest;
- the vanilla baseline needed for restoration is available.

It then stages replacements, commits them, records target ownership and hashes,
and rolls back if a transaction fails.

## Vanilla baseline

The first untouched game file observed for a managed target becomes its vanilla
baseline. The baseline is independent from legacy UMML's shared `dat.backup`
directory.

For a target that did not exist in vanilla, restoration means deleting the
manager-created target after verifying it still matches the active deployment.

The manager must never refresh vanilla from a modded file merely because a game
update or another tool changed the target.

## External-change protection

The active deployment manifest records the hash and owning mod for each managed
target. If the target later differs, UMML Manager assumes another tool, game
update, or manual operation changed it.

Normal apply stops instead of overwriting that file. Recovery may explicitly
force a new desired state, but the UI and CLI must make that decision visible.

## Providers

Providers fetch metadata and archives, then hand them to the store. They do not
prepare assets, resolve profiles, or deploy files.

The GameBanana provider records submission and selected-file identity so update
checks compare remote files with the installed source record rather than guessing
from filenames.

Future providers should implement the same boundary for GitHub releases or other
catalogs.

## Frontends

The Tk GUI and CLI share the same store, resolver, and engine. Frontends may
format plans or ask for confirmation, but they must not implement separate load
order, conflict, or backup behavior.

The frozen package uses `umml_manager_packaged.py` as a small dispatcher:

```text
umml-manager-bin gui
umml-manager-bin cli <arguments>
```

## Runtime boundary

The manager does not accept native or executable runtime plugins. Optional
in-game integration is a separate protocol and adapter.

The desktop manager retains ownership of:

- downloads and archives;
- library records and profiles;
- conflict resolution;
- vanilla backups and deployment;
- updates and rollback.

An in-game adapter may request status, queue a profile for restart, or invoke a
feature explicitly allowed for an exact game build. Unknown builds fail closed.

## Operational rule

The manager can download, import, prepare, and plan while the game runs. Applying
or restoring is blocked until the game closes. This boundary is intentionally
boring, which is an excellent property for software holding the only clean copy
of someone's game files.
