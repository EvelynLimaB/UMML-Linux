# Steam and Proton autodetection

UMML Linux uses one discovery engine in `umml_autodetect/`. It treats the Steam
client, each Steam library, the installed game, the Proton prefix, and the
writable Umamusume data directory as related but independently discoverable
objects. This matters because Steam may place the game and its prefix on
different libraries, expose either through symlinks, or move them independently.

## Discovery order

Evidence is collected and scored rather than accepted from the first path that
happens to exist:

1. Explicit `UMML_*` overrides.
2. Runtime Steam/Proton environment from `/proc/<pid>/environ`, including
   `SteamAppId`, `STEAM_COMPAT_CLIENT_INSTALL_PATH`,
   `STEAM_COMPAT_INSTALL_PATH`, and `STEAM_COMPAT_DATA_PATH`.
3. Steam roots from Debian/Mint, XDG, legacy native, Flatpak, Snap, and system
   layouts.
4. Every library from both modern and legacy `libraryfolders.vdf` layouts and
   legacy `BaseInstallFolder_*` entries in `config.vdf`.
5. `appmanifest_<appid>.acf`, ignoring manifests marked uninstalled.
6. A marker scan under each library's case-insensitive `steamapps/common`.
7. Current game-local `Persistent` data and every matching Proton prefix under
   `steamapps/compatdata/<appid>/pfx`.

When multiple valid prefixes exist, explicit/runtime evidence wins first. Among
normal library prefixes, the most recently used prefix is preferred using
`pfx.lock` modification time, matching mature Steam tooling behavior.

Paths are inspected in both symlink-preserving and canonical forms. The selected
game path remains the visible Steam path, while canonical forms are used for
deduplication and filesystem checks.

## Valve KeyValues handling

The optional `vdf` package is used when available. A standard-library parser is
kept as a fallback for frozen DEB/AppImage builds and supports comments, quoted
and bare values, escaped slashes/quotes, nested objects, and old/new Steam
library formats. Corrupt or unreadable files are skipped without preventing
other evidence from being considered.

## Diagnostics

`umml-doctor` prints all discovered roots, libraries, game candidates, data
candidates, scores, evidence sources, selected pair, and a final `READY` or
`NOT READY` result. This is intentionally verbose enough to audit a real machine
without asking the user to guess which Steam layout they have.

## Behavioral references

The implementation is original MIT-licensed UMML code. The following mature
projects were studied for Steam behavior and edge cases; their code was not
copied into this repository:

- Protontricks Steam discovery and prefix selection:
  <https://github.com/Matoking/protontricks/blob/5deec22f918ab4fef3e5348e91c353a8074e8ec6/src/protontricks/steam.py>
- Lutris Steam data-root and library configuration coverage:
  <https://github.com/lutris/lutris/blob/8663afc110c7a093f90eed8aa7fecb2829820648/lutris/util/steam/config.py>
- Valve Proton source and prefix conventions:
  <https://github.com/ValveSoftware/Proton/blob/d2bedfad453584d05308f5e3e1f9657e3f0f71d3/proton>
- Valve Proton FAQ:
  <https://github.com/ValveSoftware/Proton/wiki/Proton-FAQ>

## Regression fixtures

The test suite covers Mint/Debian Steam, lowercase XDG paths, case-insensitive
`steamapps`, Flatpak host/sandbox path translation, normal and hidden Snap
layouts, old/new library VDF formats, legacy base-install folders, secondary
libraries, process-provided paths, game/prefix separation, duplicate prefixes,
symlinked game folders, corrupt/uninstalled manifests, manual two-part
selection, and packaged DEB/AppImage smoke tests.
