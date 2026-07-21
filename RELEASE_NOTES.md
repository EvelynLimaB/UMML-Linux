# UMML 1.5.0 Linux/Proton 1

The horse game has successfully entered the penguin machine. `ฅ^•ﻌ•^ฅ`

This is the first polished Linux/Steam Proton release of UMML, based on upstream
`1.5.0-hotfix`.

## Highlights

- Steam Global detection on native Steam, Flatpak Steam, and secondary libraries
- Proton-prefix discovery with current and legacy data-layout support
- one-command user-local installation with Python 3.11, Tk, and pinned dependencies
- desktop launcher, persistent logs, and `umml-doctor`
- refreshed resizable interface with startup progress and path diagnostics
- Windows, Steam Japan, DMM Japan, and Komoe Taiwan behavior retained

## Install on Linux

Download the ZIP or tarball below, extract it, then run:

```bash
chmod +x install.sh
./install.sh
umml-doctor
umml
```

No system Python modification or reboot is required.

## Validation

- Python compilation passed
- 7/7 platform-discovery tests passed
- installer and uninstaller shell validation passed
- wrapper/core integration import passed

See `docs/LINUX.md` for path overrides and troubleshooting.
