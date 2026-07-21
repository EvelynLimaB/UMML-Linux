# UMML 1.5.0-linux.3

The game was literally open behind UMML and UMML still said “not found.” Yeah,
that was awkward. This hotfix repairs packaged Steam discovery on Linux Mint and
adds a manual escape hatch so detection cannot dead-end again. `ฅ(•ㅅ•❀)ฅ`

## Fixed

- Detects Mint/Ubuntu/Debian native Steam at `~/.steam/debian-installation`.
- Detects Steam roots and Umamusume paths from running Steam/Proton processes.
- Falls back to a built-in Valve KeyValues parser inside frozen packages.
- Finds known game folders even when `appmanifest_3224770.acf` is unavailable.
- Ignores inaccessible `/proc` entries instead of failing the whole scan.
- Shows partial states such as **Game found; data missing**.
- Offers manual Steam Global folder selection when automatic detection fails.

## Pick your package

- Mint/Ubuntu/Debian: `umml-linux_1.5.0-linux.3_amd64.deb`
- Other x86_64 Linux: `UMML-1.5.0-linux.3-x86_64.AppImage`
- Source fallback: ZIP or tarball

## Mint install

```bash
sudo apt install ./umml-linux_1.5.0-linux.3_amd64.deb
umml-doctor
umml
```

## Validation

- 11 platform and detection tests pass, including an end-to-end fake Mint layout.
- 7 release-contract tests pass.
- DEB and AppImage builds are smoke-tested for version and fake-Mint detection.
- Python compilation and shell validation pass.
