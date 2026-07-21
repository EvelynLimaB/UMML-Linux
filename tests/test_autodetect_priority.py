import os
import tempfile
import time
import unittest
from pathlib import Path

import umml_autodetect as auto


class PrefixPriorityTests(unittest.TestCase):
    def test_newer_cross_library_prefix_beats_older_game_library_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            steam = home / ".steam" / "debian-installation"
            game_library = root / "game-library"
            newer_library = root / "newer-prefix-library"
            (steam / "steamapps").mkdir(parents=True)

            game = game_library / "steamapps/common/UmamusumePrettyDerby"
            (game / auto.GLOBAL_DATA_FOLDER).mkdir(parents=True)
            (game / "UmamusumePrettyDerby.exe").write_bytes(b"")
            (game_library / "steamapps/appmanifest_3224770.acf").write_text(
                '"AppState" { "appid" "3224770" "StateFlags" "4" '
                '"installdir" "UmamusumePrettyDerby" }',
                encoding="utf-8",
            )

            def make_prefix(library: Path):
                prefix = library / "steamapps/compatdata/3224770/pfx"
                data = prefix / "drive_c/users/steamuser/AppData/LocalLow/Cygames/umamusume"
                (data / "dat").mkdir(parents=True)
                (data / "meta").write_bytes(b"meta")
                lock = prefix.parent / "pfx.lock"
                lock.write_bytes(b"")
                return data, lock

            _old_data, old_lock = make_prefix(game_library)
            new_data, new_lock = make_prefix(newer_library)
            old_time = time.time() - 1000
            new_time = time.time()
            os.utime(old_lock, (old_time, old_time))
            os.utime(new_lock, (new_time, new_time))

            (steam / "steamapps/libraryfolders.vdf").write_text(
                '"libraryfolders" {'
                f' "1" {{ "path" "{game_library}" }}'
                f' "2" {{ "path" "{newer_library}" }}'
                ' }',
                encoding="utf-8",
            )

            result = auto.discover_global_installation(
                home=home,
                environ={},
                processes=[],
            )
            self.assertTrue(result.ready)
            self.assertEqual(result.game_dir, game.absolute())
            self.assertEqual(result.data_dir, new_data.absolute())


if __name__ == "__main__":
    unittest.main()
