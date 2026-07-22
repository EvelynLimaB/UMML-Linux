# Packaging UMML and UMML Manager

This repository produces two Linux applications. They share source references and some build dependencies, but they are intentionally separate products.

| Product | Distribution formats | Commands | Version file |
| --- | --- | --- | --- |
| Legacy loader | `umml-linux` DEB/AppImage | `umml`, `umml-doctor` | `VERSION` |
| Full manager | `umml-manager` DEB/AppImage | `umml-manager`, `umml-manager-cli`, AppImage flags | `MANAGER_VERSION` |

The manager DEB, manager AppImage, source installation, and legacy loader must not merge application payload directories, desktop IDs, state paths, or version numbers. All manager formats intentionally share only the user data root, `~/.local/share/umml-manager` by default.

## Build environment

Frozen releases target x86_64 Linux and should be built on the oldest supported Ubuntu environment to preserve a reasonable glibc baseline. Current practice uses Ubuntu 22.04 / Linux Mint 21 compatibility.

Install build tools:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt -r requirements-build.txt
sudo apt install \
  appstream-util \
  curl \
  desktop-file-utils \
  dpkg-dev \
  file \
  python3-tk
```

Tkinter and the shared X11/font libraries used by the PyInstaller runtime must be available in the build image.

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

## Shared manager frozen runtime

Both manager package formats begin with exactly one build:

```bash
scripts/build_manager_frozen.sh
```

Expected bundle:

```text
build/manager-frozen/umml-manager/
└── umml-manager-bin
```

The dispatcher supports:

```text
umml-manager-bin gui
umml-manager-bin cli ...
umml-manager-bin --legacy-host ...
umml-manager-bin --version
```

The DEB and AppImage must copy this bundle unchanged. Package-specific logic belongs only in thin launchers and metadata.

## Manager Debian package

```bash
scripts/build_manager_deb.sh
```

Expected output:

```text
dist/umml-manager_<MANAGER_VERSION>_amd64.deb
```

The manager payload lives under `/usr/lib/umml-manager`:

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
│   └── ... unchanged frozen runtime ...
└── share/
    ├── applications/io.github.evelynlimab.ummlmanager.desktop
    ├── icons/hicolor/scalable/apps/io.github.evelynlimab.ummlmanager.svg
    ├── metainfo/io.github.evelynlimab.ummlmanager.metainfo.xml
    └── doc/umml-manager/
```

The wrappers select `gui` or `cli`. Keep application logic out of them.

The Debian desktop entry must use the absolute command `/usr/bin/umml-manager`. A bare `Exec=umml-manager` allows an obsolete `~/.local/bin/umml-manager` from a source preview to shadow the packaged application.

The package must not install files into the legacy `/usr/lib/umml` payload or claim `/usr/bin/umml`.

## Manager AppImage

```bash
scripts/build_manager_appimage.sh
```

Expected output:

```text
dist/umml-manager_<DISPLAY_VERSION>_x86_64.AppImage
```

Debian versions use `~`, while the portable filename uses `-`:

```text
0.2.0~alpha4  ->  umml-manager_0.2.0-alpha4_x86_64.AppImage
```

The AppDir follows the official AppDir structure:

```text
UMML_Manager.AppDir/
├── AppRun
├── .DirIcon -> io.github.evelynlimab.ummlmanager.svg
├── io.github.evelynlimab.ummlmanager.desktop
├── io.github.evelynlimab.ummlmanager.svg
└── usr/
    ├── bin/
    │   ├── umml-manager
    │   └── umml-manager-cli
    ├── lib/umml-manager/
    │   └── ... unchanged frozen runtime ...
    └── share/
        ├── applications/
        ├── icons/hicolor/scalable/apps/
        ├── metainfo/
        └── doc/umml-manager/
```

The AppImage desktop entry is separate from the Debian desktop entry. It uses `Exec=umml-manager`, which is appropriate inside an AppDir. Do not copy the Debian file with its absolute `/usr/bin` path into the AppImage.

`AppRun` behavior:

```text
no arguments      -> GUI
--version         -> version output
--cli ...         -> CLI
cli ...           -> CLI compatibility
--legacy-host ... -> Studio compatibility host
```

The build downloads the official AppImageKit `appimagetool` continuous asset over HTTPS. The tool is checked against a pinned SHA-256 before execution. If upstream replaces the continuous asset, CI must fail until the replacement is reviewed and the pin is deliberately updated.

GitHub Actions and container builds use `APPIMAGE_EXTRACT_AND_RUN=1`, avoiding a build-time dependency on a working FUSE mount.

After building, the script:

1. runs the AppImage in extraction mode and checks its reported manager version;
2. runs CLI help through the AppImage;
3. extracts the generated AppImage;
4. compares the embedded `umml-manager-bin` byte-for-byte with the source frozen bundle;
5. verifies desktop and AppStream files are present.

## Source installation boundaries

Source installation is intentionally distinguishable from both binary package formats:

```text
~/.local/share/umml-manager-app/       source application code
~/.local/share/umml-manager/           library, profiles and deployment state
~/.local/bin/umml-manager-source       source GUI
~/.local/bin/umml-manager-source-cli   source CLI
```

The source desktop ID is `io.github.evelynlimab.ummlmanager.source`. It must never reuse the Debian/AppImage desktop ID.

Compatibility wrappers named `umml-manager` and `umml-manager-cli` may exist in `~/.local/bin`, but they must explicitly prefer `/usr/bin/umml-manager*` whenever the Debian package is present.

Source uninstallers may remove only source application code, source launchers, and the source desktop/icon. They must preserve:

- `mods.json`;
- `profiles.json`;
- `settings.json`;
- `active.json`;
- `sources/`;
- `prepared/`;
- `baseline/`;
- `transactions/`;
- `downloads/`;
- `workspaces/`.

Historical previews mixed source code and manager data in `~/.local/share/umml-manager`. Migration may remove only known application payload files from that directory. Never recursively delete the directory.

## Versioning

`VERSION` tracks the Linux port of the upstream legacy loader. `MANAGER_VERSION` tracks the independently developed manager.

For pre-releases, Debian sorts `~` before the final release:

```text
0.1.0~alpha1 < 0.1.0~beta1 < 0.1.0
```

AppStream and AppImage filenames use a display-friendly equivalent such as `0.1.0-alpha1`. Keep the release date and description aligned with the manager changelog.

When changing the manager release, update together:

- `MANAGER_VERSION`;
- `MANAGER_CHANGELOG.md`;
- `README.md` and `MANAGER_README.md` examples;
- manager AppStream release entry;
- tests expecting the independent manager version;
- CI artifact names or release workflow references.

Do not embed a package's own SHA-256 inside documentation that is packaged into that same artifact. The checksum changes the file, the file changes the package, and the package changes the checksum. Generate `SHA256SUMS` externally after both packages are final.

## Validation

Static checks:

```bash
bash -n \
  install-manager.sh \
  uninstall-manager.sh \
  scripts/build_manager_frozen.sh \
  scripts/build_manager_deb.sh \
  scripts/build_manager_appimage.sh
python -m py_compile umml_manager_packaged.py umml_manager/*.py
```

Metadata checks:

```bash
desktop-file-validate \
  packaging/linux/io.github.evelynlimab.ummlmanager.desktop \
  packaging/appimage/io.github.evelynlimab.ummlmanager.desktop
appstream-util validate-relax \
  packaging/linux/io.github.evelynlimab.ummlmanager.metainfo.xml
```

Debian checks:

```bash
dpkg-deb --info dist/umml-manager_*_amd64.deb
dpkg-deb --contents dist/umml-manager_*_amd64.deb
dpkg-deb --field dist/umml-manager_*_amd64.deb Package Version Architecture
```

AppImage checks:

```bash
APPIMAGE=dist/umml-manager_*_x86_64.AppImage
file $APPIMAGE
APPIMAGE_EXTRACT_AND_RUN=1 $APPIMAGE --version
APPIMAGE_EXTRACT_AND_RUN=1 $APPIMAGE --cli --help
```

Generate external checksums:

```bash
(
  cd dist
  sha256sum \
    umml-manager_*_amd64.deb \
    umml-manager_*_x86_64.AppImage \
    > SHA256SUMS
  sha256sum -c SHA256SUMS
)
```

Debian install test:

```bash
sudo apt install ./dist/umml-manager_*_amd64.deb
/usr/bin/umml-manager-cli --version
/usr/bin/umml-manager-cli --root /tmp/umml-manager-package-test list
sudo apt remove umml-manager
```

AppImage real-desktop test:

```bash
chmod +x dist/umml-manager_*_x86_64.AppImage
dist/umml-manager_*_x86_64.AppImage
dist/umml-manager_*_x86_64.AppImage --cli --root /tmp/umml-manager-appimage-test list
```

Confirm both formats use the same XDG manager data directory and that launching one after the other does not create divergent state.

When testing coexistence with a source install, check:

```bash
type -a umml-manager
head -n 5 ~/.local/bin/umml-manager 2>/dev/null || true
grep '^Exec=' ~/.local/share/applications/io.github.evelynlimab.ummlmanager*.desktop 2>/dev/null || true
```

## CI artifacts

The manager packaging workflow:

1. installs Python and packaging dependencies;
2. compiles and tests the manager;
3. builds one manager PyInstaller bundle;
4. builds the separate Debian package;
5. builds the AppImage from the same bundle;
6. inspects and launches both formats;
7. writes and verifies external `SHA256SUMS`;
8. uploads `umml-manager-deb`, `umml-manager-appimage`, and `umml-manager-checksums` artifacts.

A CI-built package proves reproducibility of the scripted build. It does not replace installation testing on a real supported desktop.

## Release checklist

Before attaching manager packages to a public release:

- all unit and packaging jobs pass;
- the DEB installs and removes cleanly on a supported distribution;
- the AppImage starts on at least two supported distributions without relying on the repository checkout;
- GUI, CLI, auto-detection, GameBanana, and Studio work in both formats;
- the AppImage embedded binary matches the shared frozen bundle;
- stale user-level source launchers cannot impersonate the Debian build;
- source removal preserves every manager data and recovery path;
- both formats see the same library and profile state;
- a synthetic profile applies and restores correctly;
- at least one real compatible mod is imported and prepared;
- GameBanana behavior is smoke-tested against the current API;
- the game-running guard is tested under Proton;
- no game files, mod archives, decrypted metadata, user paths, or secrets are in either package;
- external checksums are published beside the final files.

Do not publish a package merely because the packaging tool agreed to put files in a box. Packaging tools are accommodating, not clairvoyant.
