import tempfile
import unittest
from pathlib import Path

import umml_autodetect as auto


class LocalLowIntegrationTests(unittest.TestCase):
    def test_manifest_game_pairs_with_uppercase_global_locallow(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            steam = home / ".steam" / "debian-installation"
            steamapps = steam / "steamapps"
            game = steamapps / "common" / "UmamusumePrettyDerby"
            data = (
                steamapps
                / "compatdata"
                / str(auto.GLOBAL_APP_ID)
                / "pfx"
                / "drive_c"
                / "users"
                / "steamuser"
                / "AppData"
                / "LocalLow"
                / "Cygames"
                / "Umamusume"
            )

            (game / auto.GLOBAL_DATA_FOLDER).mkdir(parents=True)
            (game / "UmamusumePrettyDerby.exe").write_bytes(b"")
            (data / "dat").mkdir(parents=True)
            (data / "meta").write_bytes(b"meta")
            (steamapps / f"appmanifest_{auto.GLOBAL_APP_ID}.acf").write_text(
                '"AppState" { "appid" "3224770" "StateFlags" "4" '
                '"installdir" "UmamusumePrettyDerby" }',
                encoding="utf-8",
            )

            result = auto.discover_global_installation(
                home=home,
                environ={},
                processes=[],
            )

            self.assertTrue(result.ready)
            self.assertEqual(result.game_dir, game.absolute())
            self.assertEqual(result.data_dir, data.absolute())


if __name__ == "__main__":
    unittest.main()
