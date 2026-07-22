# UMML Manager feature roadmap

This roadmap follows the alpha6 audit. Order matters: each phase creates a stable boundary needed by the next one. Skipping straight to an in-game overlay would produce a very attractive mechanism for corrupting files faster.

## Phase 1: installation targets and recovery UX

### Goal

Manage multiple Global/Japan/Taiwan installations without sharing active state, baselines, prepared metadata, or recovery material accidentally.

### Work

- Add a versioned target registry with stable target keys.
- Persist label, region, platform, game directory, `Persistent/dat`, metadata source, prepared metadata path, and last-seen fingerprints.
- Let profiles select an installation key.
- Scope active deployment state and vanilla baselines per target.
- Add a target chooser when more than one viable installation is detected.
- Surface stale metadata, interrupted transactions, and external changes in one Recovery page.
- Add explicit operations for recover, abandon untouched snapshot setup, export diagnostics, and verified baseline rebase.

### Acceptance

- Global and Japan can be managed from one library without state collisions.
- Switching targets never changes game files.
- A profile cannot deploy to a target with the wrong region.
- Legacy alpha state migrates only after matching the saved canonical path.

## Phase 2: provider and download manager

### Goal

Turn Discover into a provider-neutral catalogue and a durable download queue.

### Work

- Make GameBanana implement the provider protocol directly.
- Move provider registration into an explicit default registry.
- Add cached catalogue pages with expiry and an offline view.
- Add image caching with bounded dimensions, MIME checks, and storage quotas.
- Add resumable or restartable downloads where the server supports ranges.
- Add retry/backoff for transient HTTP failures without retrying certificate failures.
- Add download states: queued, downloading, verified, imported, failed, cancelled.
- Preserve every remote version and let the user select the active version.
- Add optional GitHub Release and local watched-folder providers.

### Acceptance

- Provider failures do not block local library/profile use.
- Downloads never overwrite an immutable prior archive.
- Every imported remote record links to exact submission, file, version, hash, size, and fetch time.
- Offline browsing clearly distinguishes cache from live results.

## Phase 3: update staging and version selection

### Goal

Make updates reversible rather than replacing whatever happened to work yesterday.

### Work

- Implement per-mod policies: notify, download only, and manual.
- Stage remote archives and source records without preparing or applying automatically.
- Compare manifests, capabilities, regions, dependencies, and conflicts before switching versions.
- Add version history and rollback in Library.
- Bulk re-prepare stale versions when the metadata fingerprint changes.
- Record which prepared version each profile selected.

### Acceptance

- No update writes game files while the game is running.
- The previous source and prepared cache remain available until deliberately pruned.
- Profile version changes are visible in the conflict plan before deployment.

## Phase 4: deployment backends

### Goal

Support multiple mod layouts without pretending they are all legacy hashed assets.

### Work

- Define prepare, plan, apply, restore, verify, and health-check backend interfaces.
- Keep the current legacy hashed-asset backend as the reference implementation.
- Add a separately packaged Hachimi runtime backend after exact-version and real-machine testing.
- Model backend-owned paths and runtime requirements in the profile plan.
- Prevent two backends from claiming the same installation path without an explicit conflict policy.
- Keep executable/native plugins outside normal archive deployment and require a separate trust flow.

### Acceptance

- Detection alone never enables an unsupported package.
- Backends declare supported platforms, regions, game builds, and restart behavior.
- Removing one backend cannot break restoration for another.

## Phase 5: native Studio and generated mods

### Goal

Replace legacy popup editors incrementally without losing any feature.

### Work

- Extract character, dress, personality, training, concert, model-swap, translation, cleanup, and database logic into headless services.
- Represent database edits as fingerprinted patches with affected tables and original rows.
- Represent asset/model edits as generated local mod workspaces.
- Add preview, diff, validation, save-as-new-version, and export.
- Keep the compatibility host until each parity row has tests and restoration coverage.
- Add operation-level game-running checks inside every headless service.

### Acceptance

- Native output can be enabled, ordered, conflicted, and restored like any other mod.
- Imported source mods remain immutable.
- Database schema changes mark patches as needing rebase instead of replaying old SQL blindly.

## Phase 6: runtime bridge and optional in-game controls

### Goal

Expose safe runtime-aware status and explicitly allowlisted actions without turning the desktop manager into an injector.

### Work

- Keep the runtime bridge separately packaged and disableable.
- Use exact game-build fingerprints and fail closed for unknown builds.
- Queue profile changes for restart unless a feature is explicitly hot-reload-safe.
- Add loopback authentication, protocol negotiation, and feature capability display.
- Build any Unity/Hachimi adapter as a separate component with its own tests and uninstall path.
- Never allow arbitrary native code through ordinary mod imports.

### Acceptance

- Unknown builds expose zero mutation features.
- The desktop manager can operate fully without the bridge.
- Runtime failure cannot prevent vanilla restoration on the next closed-game launch.

## Phase 7: polish and maintenance

- Accessible scalable fonts and keyboard navigation.
- Responsive layouts for smaller screens.
- Preview images and before/after comparison.
- Profile duplicate, rename, delete, export, and import.
- Structured logs with redaction and one-click support bundles.
- Storage quotas and safe pruning for downloads, old versions, caches, and transactions.
- Localization-ready UI strings.
- Windows package after native CI and real-machine testing.
- Release channels: alpha, beta, stable, with explicit migration notes.

## Permanent project rules

1. No legacy feature disappears before an equivalent or better replacement passes parity tests.
2. Detection is not deployment support.
3. Downloads are untrusted input even when HTTPS succeeds.
4. No game-file mutation without a closed-game check, target identity, recovery plan, and verification.
5. Source versions are immutable; edits and updates create new versions.
6. Unknown state, builds, schemas, and package types fail closed.
7. DEB and AppImage are built from one frozen runtime and compared in CI.
