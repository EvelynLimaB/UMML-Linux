# UMML 1.5.0-linux.6

The game was found. The data was there. Linux cared that the folder was named
`Umamusume` instead of `umamusume`. `.6` stops losing arguments to capital
letters. `ᕦฅ^•ﻌ•^ฅᕤ`

## Fixed

- Resolves every Proton LocalLow path component case-insensitively.
- Detects current Global data under `Cygames/Umamusume`.
- Still supports older `Cygames/umamusume` layouts.
- Performs a bounded fallback scan of LocalLow publisher/game siblings when a
  structurally valid folder contains both `meta` and `dat`.
- Keeps the scored Steam/game/prefix pairing introduced in `.5`.

## Packages

- Mint/Ubuntu/Debian: `umml-linux_1.5.0-linux.6_amd64.deb`
- Other x86_64 Linux: `UMML-1.5.0-linux.6-x86_64.AppImage`
- Source fallback: ZIP or tarball

## Mint upgrade

```bash
sudo apt install ./umml-linux_1.5.0-linux.6_amd64.deb
umml-doctor
umml
```

## Validation

- 36 local tests pass.
- Includes direct uppercase and mixed-case Wine-path tests.
- Includes an end-to-end Mint Steam manifest paired with Proton data under
  `AppData/LocalLow/Cygames/Umamusume`.
