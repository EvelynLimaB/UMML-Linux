# UMML 1.5.0-linux.4

The folder in the screenshot was valid. UMML was wrong. `.4` fixes the exact
case where Steam exposes the game through a symlink while Proton stores
`meta`/`dat` separately under `compatdata/3224770`. `(╥﹏╥) → ฅ^•ﻌ•^ฅ`

## Fixed

- Preserves the selected Steam path instead of resolving away its
  `steamapps/common` ancestry.
- Searches every detected Steam library for the matching Proton data prefix.
- Accepts the game root, `_Data`, `Persistent`, LocalLow data folder, or `dat`.
- When the game root is valid but data remains separate, asks for the data folder
  in a second dialog rather than calling the game folder incompatible.

## Packages

- Mint/Ubuntu/Debian: `umml-linux_1.5.0-linux.4_amd64.deb`
- Other x86_64 Linux: `UMML-1.5.0-linux.4-x86_64.AppImage`
- Source fallback: ZIP or tarball

## Upgrade on Mint

```bash
sudo apt install ./umml-linux_1.5.0-linux.4_amd64.deb
umml-doctor
umml
```

## Validation

The package test now reproduces the failure directly:

1. Steam lives at `~/.steam/debian-installation`.
2. The visible game folder is a symlink to another location.
3. `UmamusumePrettyDerby_Data` exists in the game folder but has no local
   Persistent metadata.
4. `meta` and `dat` exist only in Proton's `compatdata/3224770` prefix.
5. Both the finished DEB and AppImage must report `Steam Global: Detected`
   before the release can be published.
