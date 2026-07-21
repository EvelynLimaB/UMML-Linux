## Scope

- Product/layer: <!-- legacy UMML, UMML Manager, runtime bridge, packaging, docs -->
- Platforms affected: <!-- Linux/Proton, Windows, Steam Global/Japan, DMM, etc. -->

## Problem

<!-- Describe the current failure or limitation with reproducible steps. -->

## Changes

<!-- Explain the implementation and why this belongs in this layer. -->

## Safety and compatibility

- [ ] No game assets, decrypted databases, user paths, tokens, or downloaded mod archives are included.
- [ ] Game-file mutations remain blocked while the game is running.
- [ ] Existing stored state remains compatible or includes an explicit migration.
- [ ] Archive/provider input remains treated as untrusted.
- [ ] Runtime work fails closed on unknown game builds.
- [ ] Package ownership does not overlap another UMML package unexpectedly.

## Validation

<!-- Check only what applies and include exact commands/results. -->

- [ ] `bash scripts/check_legacy.sh`
- [ ] `bash scripts/check_manager.sh`
- [ ] Runtime Python tests
- [ ] `cargo test --manifest-path runtime_bridge/Cargo.toml`
- [ ] Frozen runtime built
- [ ] Debian package built and inspected
- [ ] Manual GUI smoke test
- [ ] Real game/mod smoke test

## Not tested

<!-- State unavailable platforms, live services, game builds, or hardware honestly. -->

## Release impact

- [ ] No release-note change needed
- [ ] Legacy `VERSION` / changelog / AppStream updated
- [ ] Manager `MANAGER_VERSION` / changelog / AppStream updated
