# Packaging UMML and UMML Manager

This repository produces two installable Linux applications. They share source
references and some build dependencies, but they are intentionally separate
packages.

| Product | Debian package | Commands | Version file |
| --- | --- | --- | --- |
| Legacy loader | `umml-linux` | `umml`, `umml-doctor` | `VERSION` |
| Full manager | `umml-manager` | `umml-manager`, `umml-manager-cli` | `MANAGER_VERSION` |

Neither Debian package depends on the other. Users may install either one or both.
Do not merge their payload directories, package names, desktop IDs, state paths,
or version numbers.

## Build environment

The frozen releases target x86_64 Linux and should be built on the oldest
supported Ubuntu environment to preserve a reasonable glibc baseline. Current
legacy release practice uses Ubuntu 22.04 / Linux Mint 21 compatibility.

Install build tools:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt -r requirements-build.txt
sudo apt install dpkg-dev desktop-file-utils appstream-util
```

Tkinter and the shared X11/font libraries used by the PyInstaller runtime must be
available in the build image.

## Legacy UMML package

```bash
scripts/build_frozen.sh
scripts/build_deb.sh
```

Expected output:

```text
dist/umml-linux_<VERSION>_amd64.deb
```

The legacy payload lives under `/usr/lib/umml`.

## UMML Manager package

```bash
scripts/build_manager_frozen.sh
scripts/build_manager_deb.sh
```

Expected output:

```text
dist/umml-manager_<MANAGER_VERSION>_amd64.deb
```

The manager payload lives under `/usr/lib/umml-manager`. The PyInstaller bundle
contains one dispatcher executable:

```text
/usr/lib/umml-manager/umml-manager-bin
```

Thin wrappers select the frontend:

```text
/usr/bin/umml-manager      -> umml-manager-bin gui
/usr/bin/umml-manager-cli  -> umml-manager-bin cli
```

Keep application logic out of those wrappers.

## Manager Debian layout

```text
DEBIAN/
├── control
├── md5sums
├── postinst
└── postrm
usr/
├── bin/
│   ├── umml-manager
│   └── umml-manager-cli
├── lib/umml-manager/
│   └── ... frozen runtime ...
└── share/
    ├── applications/io.github.evelynlimab.ummlmanager.desktop
    ├── icons/hicolor/scalable/apps/io.github.evelynlimab.ummlmanager.svg
    ├── metainfo/io.github.evelynlimab.ummlmanager.metainfo.xml
    └── doc/umml-manager/
```

The package must not install files into the legacy `/usr/lib/umml` payload or
claim `/usr/bin/umml`.

## Versioning

`VERSION` tracks the Linux port of the upstream legacy loader.
`MANAGER_VERSION` tracks the independently developed manager.

For pre-releases, Debian sorts `~` before the final release:

```text
0.1.0~alpha1 < 0.1.0~beta1 < 0.1.0
```

AppStream may use a display-friendly equivalent such as `0.1.0-alpha1`. Keep the
release date and description aligned with the manager changelog.

When changing the manager release, update together:

- `MANAGER_VERSION`;
- `MANAGER_CHANGELOG.md`;
- `MANAGER_README.md` examples;
- manager AppStream release entry;
- CI artifact names or release workflow references.

## Validation

Static checks:

```bash
bash -n scripts/build_manager_frozen.sh scripts/build_manager_deb.sh
python -m py_compile umml_manager_packaged.py umml_manager/*.py
```

Package checks:

```bash
dpkg-deb --info dist/umml-manager_*_amd64.deb
dpkg-deb --contents dist/umml-manager_*_amd64.deb
dpkg-deb --field dist/umml-manager_*_amd64.deb Package Version Architecture

desktop-file-validate \
  packaging/linux/io.github.evelynlimab.ummlmanager.desktop
appstream-util validate-relax \
  packaging/linux/io.github.evelynlimab.ummlmanager.metainfo.xml
```

Install test:

```bash
sudo apt install ./dist/umml-manager_*_amd64.deb
umml-manager-cli --version
umml-manager-cli --root /tmp/umml-manager-package-test list
sudo apt remove umml-manager
```

Also launch the GUI from the desktop menu. Confirm that it does not open a
terminal, uses the manager icon, and stores user data outside `/usr`.

## CI artifacts

The manager packaging workflow should:

1. install Python and packaging dependencies;
2. compile and test the manager;
3. build the manager PyInstaller bundle;
4. build the separate Debian package;
5. inspect package metadata and contents;
6. upload the `.deb` as a workflow artifact.

A CI-built package proves reproducibility of the scripted build. It does not
replace installation testing on a real supported desktop.

## Release checklist

Before attaching a manager DEB to a public release:

- all unit and packaging jobs pass;
- the package installs and removes cleanly on a supported distribution;
- GUI and CLI both start from the installed package;
- a synthetic profile applies and restores correctly;
- at least one real compatible mod is imported and prepared;
- GameBanana behavior is smoke-tested against the current API;
- the game-running guard is tested under Proton;
- no game files, mod archives, decrypted metadata, user paths, or secrets are in
  the package;
- checksums are generated for published artifacts.

Do not publish a package merely because `dpkg-deb` agreed to put files in a box.
It is an accommodating tool, not a quality-assurance department.
