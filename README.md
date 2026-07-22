# UMML for Linux

[![Latest release](https://img.shields.io/github/v/release/EvelynLimaB/UMML-Linux?display_name=tag&sort=semver)](https://github.com/EvelynLimaB/UMML-Linux/releases/latest)
[![Python checks](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml/badge.svg)](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/python-checks.yml)
[![Manager checks](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/manager-checks.yml/badge.svg)](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/manager-checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-7651a8.svg)](LICENSE)

Linux, Steam Proton, packaging, and mod-management work for **Umamusume Pretty Derby**.

| Application | Purpose | Package | Commands |
| --- | --- | --- | --- |
| **Legacy UMML** | One-folder loader, preview, backup, restore, and direct editors | `umml-linux` | `umml`, `umml-doctor` |
| **UMML Manager** | Mod library, profiles, GameBanana browser, local detection, conflicts, Studio editors, and transactional deployment | `umml-manager` | `umml-manager`, `umml-manager-cli` |

They can coexist and do not own the same application files or backup state.

> Close the game before either application writes, restores, or edits game data. Downloading, scanning, importing, browsing, preparing, and conflict planning may happen while it runs.

## Downloads

### Legacy UMML

Stable Linux release: **`1.5.0-linux.6`**.

```bash
sudo apt install ./umml-linux_1.5.0-linux.6_amd64.deb
umml-doctor
umml
```

Download the DEB or AppImage from [GitHub Releases](https://github.com/EvelynLimaB/UMML-Linux/releases/latest).

### UMML Manager preview

Current manager preview: **`0.2.0~alpha3`**, developed in [draft PR #2](https://github.com/EvelynLimaB/UMML-Linux/pull/2).

Until it becomes a permanent Release asset, download the latest `umml-manager-deb` artifact from the [manager branch workflow runs](https://github.com/EvelynLimaB/UMML-Linux/actions/workflows/manager-checks.yml?query=branch%3Aagent%2Fumml-manager-foundation).

```bash
sudo apt install ./umml-manager_0.2.0~alpha3_amd64.deb
/usr/bin/umml-manager
```

Using the absolute command is useful when testing upgrades from early source previews. Alpha3 also makes the desktop launcher use `/usr/bin/umml-manager` directly so `~/.local/bin` cannot silently start an older copy.

Current CI artifact DEB SHA-256:

```text
4e446e27a81280336d539279dda9457cce0e9d85c38cd1ccfdd9d52fc0aabe1e
```

## Manager highlights

- guided first-launch Steam/Proton detection and metadata preparation;
- polished dark sidebar interface;
- immutable installed-mod source versions;
- named profiles and explicit load order;
- per-file conflict explanations;
- deployment blocked for missing or unprepared enabled mods;
- transactional apply, rollback, and vanilla restoration;
- corrupt manager state fails closed rather than becoming empty state;
- automatic nested mod-folder and archive detection;
- built-in browsing of Global and Japan Umamusume GameBanana mods;
- search, sorting, statistics, file selection, download, and direct import;
- editable workspace copies that preserve downloaded originals;
- complete legacy editing features through the built-in Studio compatibility host;
- character, personality, dress, training, concert, model-swap, translation, cleanup, database, preview, manual-load, and restore tools;
- Linux/Proton and Windows game-running guards;
- independent frozen runtime and Debian package.

Read [MANAGER_README.md](MANAGER_README.md) for the complete workflow and the one-time cleanup instructions for early alpha source installs.

## Basic manager workflow

1. Open the manager and let **Settings** auto-detect the game and prepare metadata.
2. Browse GameBanana or scan Downloads/custom folders in **Discover**.
3. Import, prepare, enable, and order mods in **Library**.
4. Inspect **Conflicts**. Missing or unprepared entries block deployment.
5. Close the game and apply the profile.
6. Use **Studio** for the original loader's editing tools.

## Source installation

```bash
# Legacy loader
chmod +x install.sh
./install.sh

# Manager
chmod +x install-manager.sh uninstall-manager.sh
./install-manager.sh
```

The current source installer keeps application code in `~/.local/share/umml-manager-app`, manager data in `~/.local/share/umml-manager`, and exposes explicit `umml-manager-source` commands. Generic compatibility commands prefer the Debian package whenever it is installed.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-build.txt
bash scripts/check_legacy.sh
bash scripts/check_manager.sh
```

Documentation starts at [docs/README.md](docs/README.md). Contribution rules are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Runtime bridge

The experimental runtime bridge is a separate, fail-closed component and is not included in the manager DEB. It does not yet inject into Unity or provide an in-game overlay.

## License

MIT. Third-party mods and downloads retain their original licenses.
