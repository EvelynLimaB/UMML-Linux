# Contributing

## Scope

Keep platform-specific discovery in `umml_platform.py`. Avoid scattering direct
registry, Steam, or Proton path logic through the GUI. Existing Windows, Steam
Japan, DMM, Komoe, and Linux behavior must remain usable when adding a platform.

Do not commit:

- Python or Micromamba environments
- generated databases or decrypted metadata
- `dat`, `dat.backup`, game assets, or mod archives
- logs, caches, or user-specific paths

## Setup

```bash
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
# Packaging work also needs: python -m pip install -r requirements-build.txt
```

Linux development also requires a Python build with Tk support.

## Required checks

```bash
python -m py_compile UMML.py UMML_core.py umml_platform.py umml_packaged.py
python -m unittest discover -s tests -v
bash -n install.sh uninstall.sh scripts/*.sh
scripts/build_release.sh
```

For GUI changes, manually verify:

1. the startup window renders before path scanning;
2. the platform chooser remains in front of the main window;
3. resizing does not hide the mod path, actions, or progress bar;
4. loading, backup creation, restoration, and diagnostic reporting still work;
5. error dialogs are parented to the UMML window.

## Pull requests

Explain the affected platform, why the change is needed, compatibility risks,
and the exact checks performed. Keep source changes reviewable; do not submit a
binary-only bundle.

## Binary packages

The DEB and AppImage share the PyInstaller runtime produced by
`scripts/build_frozen.sh`. Keep package-specific launchers thin and do not fork
the Python application logic between formats. Binary packages currently target
x86_64 and are built on Ubuntu 22.04 for a Linux Mint 21-compatible glibc
baseline.

Before changing a release, update `VERSION`, `CHANGELOG.md`,
`RELEASE_NOTES.md`, and the AppStream release entry together.
