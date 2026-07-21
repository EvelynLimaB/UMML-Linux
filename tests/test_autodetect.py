import os
import tempfile
import time
import unittest
from pathlib import Path

import umml_autodetect as auto


class AutoDetectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def make_game(self, library, name="UmamusumePrettyDerby", local_data=True):
        steamapps = library / "steamapps"
        game = steamapps / "common" / name
        data = game / auto.GLOBAL_DATA_FOLDER / "Persistent"
        game.mkdir(parents=True)
        (game / "UmamusumePrettyDerby.exe").write_bytes(b"")
        if local_data:
            (data / "dat").mkdir(parents=True)
            (data / "meta").write_bytes(b"meta")
        manifest = steamapps / f"appmanifest_{auto.GLOBAL_APP_ID}.acf"
        manifest.write_text(
            '"AppState"\n{\n"appid" "3224770"\n"StateFlags" "4"\n"installdir" "%s"\n}\n' % name,
            encoding="utf-8",
        )
        return game, data

    def make_prefix(self, library, user="steamuser"):
        prefix = library / "steamapps" / "compatdata" / str(auto.GLOBAL_APP_ID) / "pfx"
        data = prefix / "drive_c" / "users" / user / "AppData" / "LocalLow" / "Cygames" / "umamusume"
        (data / "dat").mkdir(parents=True)
        (data / "meta").write_bytes(b"meta")
        (prefix.parent / "pfx.lock").write_bytes(b"")
        return prefix, data

    def test_mint_root_and_local_data(self):
        library = self.home / ".steam" / "debian-installation"
        game, data = self.make_game(library)
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)
        self.assertEqual(result.game_dir, game.absolute())
        self.assertEqual(result.data_dir, data.absolute())

    def test_lowercase_xdg_and_casefold_steamapps(self):
        library = self.home / ".local" / "share" / "steam"
        steamapps = library / "SteaMAPps"
        game = steamapps / "COMMON" / "UmamusumePrettyDerby"
        data = game / auto.GLOBAL_DATA_FOLDER / "Persistent"
        (data / "dat").mkdir(parents=True)
        (data / "meta").write_bytes(b"meta")
        (game / "UmamusumePrettyDerby.exe").write_bytes(b"")
        (steamapps / f"appmanifest_{auto.GLOBAL_APP_ID}.acf").write_text(
            '"AppState" { "AppID" "3224770" "installdir" "UmamusumePrettyDerby" }'
        )
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)
        self.assertEqual(result.game_dir, game.absolute())

    def test_new_and_old_libraryfolders(self):
        root = self.home / ".local/share/Steam"
        (root / "steamapps").mkdir(parents=True)
        secondary = self.root / "Games" / "SteamLibrary"
        self.make_game(secondary)
        (root / "steamapps/libraryfolders.vdf").write_text(
            f'"libraryfolders" {{ "1" {{ "path" "{secondary}" "mounted" "1" }} }}'
        )
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)
        self.assertEqual(result.game_dir, (secondary / "steamapps/common/UmamusumePrettyDerby").absolute())

        (root / "steamapps/libraryfolders.vdf").write_text(
            f'"libraryfolders" {{ "1" "{secondary}" }}'
        )
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)

    def test_config_baseinstallfolder_fallback(self):
        root = self.home / ".local/share/Steam"
        (root / "steamapps").mkdir(parents=True)
        secondary = self.root / "LibraryTwo"
        self.make_game(secondary)
        (root / "config").mkdir()
        (root / "config/config.vdf").write_text(
            f'"InstallConfigStore" {{ "Software" {{ "Valve" {{ "Steam" {{ "BaseInstallFolder_1" "{secondary}" }} }} }} }}'
        )
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)

    def test_game_and_prefix_on_different_libraries(self):
        root = self.home / ".steam/debian-installation"
        (root / "steamapps").mkdir(parents=True)
        game_lib = self.root / "Games"
        prefix_lib = self.root / "Prefixes"
        game, _ = self.make_game(game_lib, local_data=False)
        _, data = self.make_prefix(prefix_lib)
        (root / "steamapps/libraryfolders.vdf").write_text(
            f'"libraryfolders" {{ "1" {{ "path" "{game_lib}" }} "2" {{ "path" "{prefix_lib}" }} }}'
        )
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)
        self.assertEqual(result.game_dir, game.absolute())
        self.assertEqual(result.data_dir, data.absolute())

    def test_newest_prefix_wins_across_libraries(self):
        root = self.home / ".steam/debian-installation"
        (root / "steamapps").mkdir(parents=True)
        game_lib = self.root / "Games"
        old_lib = self.root / "OldPrefixes"
        new_lib = self.root / "NewPrefixes"
        self.make_game(game_lib, local_data=False)
        old_prefix, _ = self.make_prefix(old_lib)
        new_prefix, new_data = self.make_prefix(new_lib)
        old_time = time.time() - 1000
        new_time = time.time()
        os.utime(old_prefix.parent / "pfx.lock", (old_time, old_time))
        os.utime(new_prefix.parent / "pfx.lock", (new_time, new_time))
        (root / "steamapps/libraryfolders.vdf").write_text(
            f'"libraryfolders" {{ "1" {{ "path" "{game_lib}" }} "2" {{ "path" "{old_lib}" }} "3" {{ "path" "{new_lib}" }} }}'
        )
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)
        self.assertEqual(result.data_dir, new_data.absolute())

    def test_symlink_game_preserved_with_separate_prefix(self):
        root = self.home / ".steam/debian-installation"
        common = root / "steamapps/common"
        common.mkdir(parents=True)
        real = self.root / "real/game"
        (real / auto.GLOBAL_DATA_FOLDER).mkdir(parents=True)
        (real / "UmamusumePrettyDerby.exe").write_bytes(b"")
        visible = common / "UmamusumePrettyDerby"
        visible.symlink_to(real, target_is_directory=True)
        (root / "steamapps" / f"appmanifest_{auto.GLOBAL_APP_ID}.acf").write_text(
            '"AppState" { "appid" "3224770" "installdir" "UmamusumePrettyDerby" }'
        )
        _, data = self.make_prefix(root)
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)
        self.assertEqual(result.game_dir, visible.absolute())
        self.assertEqual(result.data_dir, data.absolute())

    def test_process_environment_is_authoritative(self):
        root = self.root / "odd-steam"
        game, _ = self.make_game(root, local_data=False)
        _, data = self.make_prefix(root)
        compat = root / "steamapps/compatdata" / str(auto.GLOBAL_APP_ID)
        proc = auto.ProcessEvidence(
            pid=42,
            app_id=auto.GLOBAL_APP_ID,
            env={
                "STEAM_COMPAT_CLIENT_INSTALL_PATH": str(root),
                "STEAM_COMPAT_DATA_PATH": str(compat),
                "STEAM_COMPAT_INSTALL_PATH": str(game),
                "SteamAppId": str(auto.GLOBAL_APP_ID),
            },
            cwd=game,
            exe=game / "UmamusumePrettyDerby.exe",
            argv=(str(game / "UmamusumePrettyDerby.exe"),),
        )
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[proc])
        self.assertTrue(result.ready)
        self.assertEqual(result.game_dir, game.absolute())
        self.assertEqual(result.data_dir, data.absolute())

    def test_uninstalled_manifest_is_ignored_but_marker_scan_works(self):
        library = self.home / ".local/share/Steam"
        game, _ = self.make_game(library)
        (library / "steamapps" / f"appmanifest_{auto.GLOBAL_APP_ID}.acf").write_text(
            '"AppState" { "appid" "3224770" "StateFlags" "1" "installdir" "Wrong" }'
        )
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)
        self.assertEqual(result.game_dir, game.absolute())

    def test_manual_accepts_game_or_data_and_two_step(self):
        library = self.home / ".steam/debian-installation"
        game, _ = self.make_game(library, local_data=False)
        _, data = self.make_prefix(library)
        self.assertTrue(auto.manual_global_installation(game, home=self.home, environ={}, processes=[]).ready)
        self.assertTrue(auto.manual_global_installation(data, home=self.home, environ={}, processes=[]).ready)
        self.assertTrue(auto.manual_global_installation(game, data, home=self.home, environ={}, processes=[]).ready)

    def test_flatpak_internal_xdg_path_maps_to_host_sandbox(self):
        flatpak = self.home / ".var/app/com.valvesoftware.Steam/.local/share/Steam"
        game, data = self.make_game(flatpak)
        (flatpak / "steamapps/libraryfolders.vdf").write_text(
            f'"libraryfolders" {{ "0" {{ "path" "{self.home / ".local/share/Steam"}" }} }}'
        )
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)
        self.assertEqual(result.game_dir, game.absolute())
        self.assertEqual(result.data_dir, data.absolute())

    def test_snap_hidden_root(self):
        snap = self.home / ".snap/data/steam/common/.local/share/Steam"
        game, data = self.make_game(snap)
        result = auto.discover_global_installation(home=self.home, environ={}, processes=[])
        self.assertTrue(result.ready)
        self.assertEqual(result.game_dir, game.absolute())
        self.assertEqual(result.data_dir, data.absolute())

    def test_scan_processes_reads_runtime_environment(self):
        proc = self.root / "proc"
        pid = proc / "123"
        pid.mkdir(parents=True)
        (pid / "environ").write_bytes(
            b"SteamAppId=3224770\0STEAM_COMPAT_CLIENT_INSTALL_PATH=/games/Steam\0"
            b"STEAM_COMPAT_DATA_PATH=/games/Steam/steamapps/compatdata/3224770\0"
        )
        (pid / "cmdline").write_bytes(b"/games/Uma/UmamusumePrettyDerby.exe\0")
        found = auto.scan_processes(proc)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].app_id, auto.GLOBAL_APP_ID)
        self.assertEqual(found[0].env["STEAM_COMPAT_CLIENT_INSTALL_PATH"], "/games/Steam")

    def test_symlinked_duplicate_steam_roots_are_deduplicated(self):
        real = self.root / "real-steam"
        (real / "steamapps").mkdir(parents=True)
        link = self.home / ".steam/debian-installation"
        link.parent.mkdir(parents=True)
        link.symlink_to(real, target_is_directory=True)
        roots = auto.discover_steam_roots(
            home=self.home,
            environ={"UMML_STEAM_ROOT": str(real)},
            processes=[],
        )
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0].source, "environment:UMML_STEAM_ROOT")

    def test_vdf_comments_escapes_and_corruption(self):
        parsed = auto.parse_vdf_text('// hi\n"root" { "path" "C:\\\\Games" bare value }')
        self.assertEqual(parsed["root"]["path"], "C:\\Games")
        self.assertEqual(parsed["root"]["bare"], "value")
        with self.assertRaises(auto.VDFError):
            auto.parse_vdf_text('"root" { "x"')


if __name__ == "__main__":
    unittest.main()
