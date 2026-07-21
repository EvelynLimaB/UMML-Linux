import tempfile
import unittest
from pathlib import Path

from umml_autodetect.locallow import iter_locallow_data_dirs


class LocalLowDetectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.prefix = self.root / "pfx"

    def tearDown(self):
        self.temp.cleanup()

    def make_data(self, relative: str) -> Path:
        target = self.prefix / relative
        (target / "dat").mkdir(parents=True)
        (target / "meta").write_bytes(b"meta")
        return target

    def detected(self) -> list[Path]:
        return list(iter_locallow_data_dirs(self.prefix))

    def test_global_uppercase_umamusume_folder(self):
        target = self.make_data(
            "drive_c/users/steamuser/AppData/LocalLow/Cygames/Umamusume"
        )
        self.assertEqual(self.detected(), [target.absolute()])

    def test_every_windows_component_is_case_insensitive(self):
        target = self.make_data(
            "DRIVE_C/Users/SteamUser/appdata/locallow/CYGAMES/UMAMUSUME"
        )
        self.assertEqual(self.detected(), [target.absolute()])

    def test_valid_sibling_name_is_discovered_boundedly(self):
        target = self.make_data(
            "drive_c/users/steamuser/AppData/LocalLow/Cygames/UmamusumePrettyDerby"
        )
        self.assertEqual(self.detected(), [target.absolute()])

    def test_invalid_folder_is_not_returned(self):
        target = self.prefix / "drive_c/users/steamuser/AppData/LocalLow/Cygames/Umamusume"
        target.mkdir(parents=True)
        (target / "meta").write_bytes(b"meta")
        self.assertEqual(self.detected(), [])


if __name__ == "__main__":
    unittest.main()
