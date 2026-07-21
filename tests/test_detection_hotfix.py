import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import umml_detection_hotfix as hotfix
import umml_platform as platform


class DetectionHotfixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.env = mock.patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.home_patch = mock.patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()
        hotfix.apply()

    def tearDown(self):
        self.home_patch.stop()
        self.env.stop()
        self.temp.cleanup()

    def make_mint_layout(self):
        steam = self.home / ".steam" / "debian-installation"
        game = steam / "steamapps" / "common" / "Umamusume Pretty Derby"
        persistent = game / "UmamusumePrettyDerby_Data" / "Persistent"
        (persistent / "dat").mkdir(parents=True)
        (persistent / "meta").write_bytes(b"meta")
        manifest = steam / "steamapps" / f"appmanifest_{platform.GLOBAL_STEAM_APP_ID}.acf"
        manifest.write_text(
            '"AppState"\n{\n  "installdir" "Umamusume Pretty Derby"\n}\n',
            encoding="utf-8",
        )
        return steam, game, persistent

    def test_mint_debian_installation_is_detected_end_to_end(self):
        steam, game, persistent = self.make_mint_layout()
        with mock.patch("umml_detection_hotfix._running_process_paths", return_value=[]):
            installation = next(
                item for item in platform.detect_installations()
                if item.key == "steam-global"
            )
        self.assertIn(str(steam.resolve()), platform.steam_root_candidates())
        self.assertTrue(installation.detected)
        self.assertEqual(installation.game_dir, game.resolve())
        self.assertEqual(installation.data_dir, persistent.resolve())

    def test_fallback_parser_reads_manifest_and_library_path(self):
        steam, _, _ = self.make_mint_layout()
        manifest = steam / "steamapps" / f"appmanifest_{platform.GLOBAL_STEAM_APP_ID}.acf"
        parsed = hotfix._fallback_vdf(manifest)
        self.assertEqual(parsed["AppState"]["installdir"], "Umamusume Pretty Derby")

        secondary = self.root / "Games" / "SteamLibrary"
        secondary.mkdir(parents=True)
        libraries = steam / "steamapps" / "libraryfolders.vdf"
        libraries.write_text(
            f'"libraryfolders"\n{{\n "1" {{ "path" "{secondary}" }}\n}}\n',
            encoding="utf-8",
        )
        parsed = hotfix._fallback_vdf(libraries)
        self.assertEqual(parsed["libraryfolders"]["0"]["path"], str(secondary))

    def test_manual_game_folder_accepts_current_persistent_layout(self):
        _, game, persistent = self.make_mint_layout()
        item = hotfix._manual_global(game)
        self.assertIsNotNone(item)
        self.assertTrue(item.detected)
        self.assertEqual(item.data_dir, persistent.resolve())

    def test_permission_restricted_process_paths_do_not_abort(self):
        denied = self.root / "denied"
        with mock.patch.object(Path, "resolve", side_effect=PermissionError("denied")):
            self.assertIsNone(hotfix._steam_root_from_path(denied))


if __name__ == "__main__":
    unittest.main()
