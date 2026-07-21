import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import umml_platform as platform


class PlatformDetectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.env = mock.patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.home_patch = mock.patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()

    def tearDown(self):
        self.home_patch.stop()
        self.env.stop()
        self.temp.cleanup()

    def make_global_layout(self):
        game = self.root / "SteamLibrary" / "steamapps" / "common" / "Uma Global"
        persistent = game / "UmamusumePrettyDerby_Data" / "Persistent"
        (persistent / "dat").mkdir(parents=True)
        (persistent / "meta").write_bytes(b"sqlite-placeholder")
        return game, persistent

    def test_steam_root_candidates_include_native_and_flatpak(self):
        native = self.home / ".local" / "share" / "Steam"
        flatpak = (
            self.home
            / ".var"
            / "app"
            / "com.valvesoftware.Steam"
            / ".local"
            / "share"
            / "Steam"
        )
        native.mkdir(parents=True)
        flatpak.mkdir(parents=True)

        roots = platform.steam_root_candidates()
        self.assertIn(str(native.resolve()), roots)
        self.assertIn(str(flatpak.resolve()), roots)

    def test_secondary_steam_library_is_read(self):
        steam = self.home / ".local" / "share" / "Steam"
        secondary = self.root / "SecondaryLibrary"
        (steam / "steamapps").mkdir(parents=True)
        secondary.mkdir()
        (steam / "steamapps" / "libraryfolders.vdf").write_text("placeholder")

        parsed = {"libraryfolders": {"0": {"path": str(steam)}, "1": {"path": str(secondary)}}}
        with mock.patch("umml_platform._load_vdf", return_value=parsed):
            libraries = platform.get_steam_libraries(str(steam))

        self.assertEqual(libraries, [str(steam.resolve()), str(secondary.resolve())])

    def test_find_game_path_from_manifest(self):
        library = self.root / "Library"
        manifest = library / "steamapps" / f"appmanifest_{platform.GLOBAL_STEAM_APP_ID}.acf"
        game = library / "steamapps" / "common" / "Uma Global"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("placeholder")
        game.mkdir(parents=True)

        with mock.patch("umml_platform.get_steam_libraries", return_value=[str(library)]), mock.patch(
            "umml_platform._load_vdf",
            return_value={"AppState": {"installdir": "Uma Global"}},
        ):
            detected = platform.find_game_path(platform.GLOBAL_STEAM_APP_ID)

        self.assertEqual(detected, str(game.resolve()))

    def test_find_proton_locallow(self):
        library = self.root / "Library"
        locallow = (
            library
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
        locallow.mkdir(parents=True)
        (locallow / "meta").write_bytes(b"meta")

        with mock.patch("umml_platform.get_steam_libraries", return_value=[str(library)]):
            detected = platform.find_proton_locallow(platform.GLOBAL_STEAM_APP_ID)

        self.assertEqual(detected, locallow.resolve())

    def test_forced_global_selection_uses_overrides(self):
        game, persistent = self.make_global_layout()
        os.environ.update(
            {
                "UMML_GAME_DIR": str(game),
                "UMML_PERSISTENT_DIR": str(persistent),
                "UMML_PLATFORM": "steam-global",
            }
        )

        dat, backup, region, game_dir, meta = platform.load_settings()

        self.assertEqual(dat, str((persistent / "dat").resolve()))
        self.assertEqual(backup, str((persistent / "dat.backup").resolve()))
        self.assertEqual(region, "Global")
        self.assertEqual(game_dir, str(game.resolve()))
        self.assertEqual(meta, str((persistent / "meta").resolve()))

    def test_komoe_layout_keeps_meta_and_dat_at_game_root(self):
        game = self.root / "Komoe" / "komoemumamusume Game"
        (game / "dat").mkdir(parents=True)
        (game / "meta").write_bytes(b"meta")
        (game / "komoeumamusume_Data" / "Persistent").mkdir(parents=True)
        os.environ["UMML_KOMOE_GAME_DIR"] = str(game)

        installation = next(
            item for item in platform.detect_installations() if item.key == "komoe-tw"
        )

        self.assertTrue(installation.detected)
        self.assertEqual(installation.meta_path, game / "meta")
        self.assertEqual(installation.dat_path, game / "dat")

    def test_kakao_is_visible_but_disabled(self):
        installation = next(
            item for item in platform.detect_installations() if item.key == "kakao-kr"
        )
        self.assertFalse(installation.supported)
        self.assertEqual(installation.status_text, "Not implemented")


if __name__ == "__main__":
    unittest.main()
