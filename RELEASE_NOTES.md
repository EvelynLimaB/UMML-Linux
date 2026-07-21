# UMML 1.5.0-linux.5

No more path-fix lasagna. `.5` replaces the emergency patch stack with one
proper Steam/Proton discovery engine. `ᕦฅ^•ﻌ•^ฅᕤ`

## What changed

- One autodetection package is used by source, DEB, and AppImage launches.
- Steam client roots, secondary libraries, game installs, Proton prefixes, and
  writable data are discovered independently and paired by evidence.
- Handles Mint/Debian, XDG case variants, Flatpak, Snap, legacy Steam links,
  old/new library VDF formats, case differences, symlinks, and split libraries.
- Reads live Proton environment variables from the running user's processes.
- Uses the newest valid `pfx` when duplicate prefixes exist.
- Falls back from corrupt/missing manifests to marker scans and a built-in
  Valve KeyValues parser.
- `umml-doctor` explains every candidate and why the selected pair won.

## Packages

- Mint/Ubuntu/Debian: `umml-linux_1.5.0-linux.5_amd64.deb`
- Other x86_64 Linux: `UMML-1.5.0-linux.5-x86_64.AppImage`
- Source fallback: ZIP or tarball

## Mint upgrade

```bash
sudo apt install ./umml-linux_1.5.0-linux.5_amd64.deb
umml-doctor
umml
```

## Validation

- 31 local tests pass.
- Release CI builds the real source archives, DEB and AppImage.
- Both finished binary packages must detect a symlinked game on one secondary
  Steam library and its Proton prefix on another before publication.
