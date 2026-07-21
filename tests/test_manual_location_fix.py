import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import umml_detection_hotfix as detection
import umml_manual_location_fix as manual
import umml_platform as platform


class ManualLocationFixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.env = mock.patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.home_patch = mock.patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()
        self.process_patch = mock.patch(
            "umml_detection_hotfix._running_process_paths",
            return_value=[],
        )
        self.process_patch.start()
        detection.apply()
        manual.apply()

    def tearDown(self):
        self.process_patch.stop()
        self.home_patch.stop()
        self.env.stop()
        self.temp.cleanup()

    def make_symlinked_proton_layout(self):
        steam = self.home / ".steam" / "debian-installation"
        common = steam / "steamapps" / "common"
        common.mkdir(parents=True)

        real_game = self.root / "games" / "UmamusumePrettyDerby"
        (real_game / "UmamusumePrettyDerby_Data").mkdir(parents=True)
        (real_game / "UmamusumePrettyDerby.exe").write_bytes(b"")

        visible_game = common / "UmamusumePrettyDerby"
        visible_game.symlink_to(real_game, target_is_directory=True)

        data = (
            steam
            / "steamapps"
            / "compatdata"
            / str(platform.GLOBAL_STEAM_APP_ID)
            / "pfx"
            / "drive_c"
            / "users"
            / "steamuser"
            / "AppData"
            / "LocalLow"
            / "Cygames"
            / "umamusume"
        )
        (data / "dat").mkdir(parents=True)
        (data / "meta").write_bytes(b"meta")
        return steam, visible_game, real_game, data

    def test_selected_symlink_game_uses_separate_proton_data(self):
        _, visible_game, _, data = self.make_symlinked_proton_layout()
        item = manual._manual_global(visible_game)

        self.assertIsNotNone(item)
        self.assertTrue(item.detected)
        self.assertEqual(item.game_dir, visible_game.absolute())
        self.assertEqual(item.data_dir, data.absolute())

    def test_selecting_data_folder_separately_completes_game_selection(self):
        _, visible_game, _, data = self.make_symlinked_proton_layout()
        with mock.patch.object(manual, "_find_proton_data", return_value=None):
            item = manual._manual_global(visible_game, data)

        self.assertIsNotNone(item)
        self.assertTrue(item.detected)
        self.assertEqual(item.game_dir, visible_game.absolute())
        self.assertEqual(item.data_dir, data.absolute())

    def test_data_and_data_subfolder_are_accepted(self):
        _, visible_game, _, data = self.make_symlinked_proton_layout()
        for selected_data in (data, data / "dat"):
            with self.subTest(selected_data=selected_data):
                item = manual._manual_global(visible_game, selected_data)
                self.assertIsNotNone(item)
                self.assertTrue(item.detected)

    def test_data_folder_without_game_uses_detected_game(self):
        _, visible_game, _, data = self.make_symlinked_proton_layout()
        with mock.patch.object(
            platform,
            "find_game_path",
            return_value=str(visible_game),
        ):
            item = manual._manual_global(data)

        self.assertIsNotNone(item)
        self.assertTrue(item.detected)
        self.assertEqual(item.data_dir, data.absolute())


if __name__ == "__main__":
    unittest.main()
