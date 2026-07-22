import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from umml_manager.discovery import scan_mod_candidates
from umml_manager.engine import ApplyEngine, ApplyError
from umml_manager.installations import InstallationError, detect_preferred_installation
from umml_manager.models import ModRecord, Profile
from umml_manager.providers.gamebanana import GameBananaClient
from umml_manager.resolver import resolve_profile
from umml_manager.store import ManagerStore, StoreError, hash_file
from umml_manager.version import manager_version


class JsonResponse(io.BytesIO):
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class ManagerTests(unittest.TestCase):
    def test_version_comes_from_independent_manager_version_file(self):
        self.assertEqual(manager_version(), "0.2.0~alpha2")

    def test_resolver_uses_profile_order_and_reports_conflict(self):
        first = ModRecord("a", "A", prepared_path="/a", files={"aa/aafile": "one"})
        second = ModRecord("b", "B", prepared_path="/b", files={"aa/aafile": "two"})
        result = resolve_profile(Profile("Default", ["a", "b"]), [first, second])
        self.assertEqual(result.winners["aa/aafile"].mod_id, "b")
        self.assertEqual(result.conflicts[0].overridden, ("a",))

    def test_archive_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("../escape", "bad")
            with self.assertRaises(StoreError):
                ManagerStore(root / "manager").import_archive(archive)

    def test_nested_mod_folder_is_detected_and_imported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mod = root / "Downloads" / "author-package" / "actual-mod"
            (mod / "assets").mkdir(parents=True)
            (mod / "assets" / "texture.bundle").write_bytes(b"asset")
            (mod / "setting.json").write_text(
                json.dumps({"title": "Detected mod", "mod_version": "2"}), encoding="utf-8"
            )
            candidates = scan_mod_candidates([root / "Downloads"])
            self.assertEqual([item.path for item in candidates], [mod])
            record = ManagerStore(root / "manager").import_folder(root / "Downloads")
            self.assertEqual(record.name, "Detected mod")
            self.assertEqual(record.version, "2")

    def test_workspace_is_a_copy_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mod = root / "mod"
            (mod / "assets").mkdir(parents=True)
            (mod / "assets" / "file").write_text("original")
            (mod / "setting.json").write_text('{"title":"Editable","mod_version":"1"}')
            store = ManagerStore(root / "manager")
            record = store.import_folder(mod)
            workspace = store.create_workspace(record.id)
            (workspace / "assets" / "file").write_text("edited")
            self.assertEqual((Path(record.source_path) / "assets" / "file").read_text(), "original")
            self.assertTrue((workspace / ".umml-workspace.json").is_file())

    def test_installation_detection_prefers_region_and_prepares_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            global_game = root / "global-game"
            global_dat = root / "global-persistent" / "dat"
            global_meta = root / "global-persistent" / "meta"
            global_dec = root / "global-persistent" / "meta_decrypted_test.db"
            japan_game = root / "japan-game"
            japan_dat = root / "japan-persistent" / "dat"
            japan_meta = root / "japan-persistent" / "meta"
            for directory in (global_game, global_dat, japan_game, japan_dat):
                directory.mkdir(parents=True)
            for path in (global_meta, global_dec, japan_meta):
                path.write_bytes(b"db")
            installs = [
                SimpleNamespace(
                    key="steam-japan",
                    label="Steam Japan",
                    region="Japan",
                    game_dir=japan_game,
                    dat_path=japan_dat,
                    meta_path=japan_meta,
                    detected=True,
                ),
                SimpleNamespace(
                    key="steam-global",
                    label="Steam Global",
                    region="Global",
                    game_dir=global_game,
                    dat_path=global_dat,
                    meta_path=global_meta,
                    detected=True,
                ),
            ]
            calls = []

            def decryptor(dat_path, meta_path, region):
                calls.append((dat_path, meta_path, region))
                return global_dec

            with patch("umml_platform.detect_installations", return_value=installs):
                selected = detect_preferred_installation("global", decryptor=decryptor)
            self.assertEqual(selected.key, "steam-global")
            self.assertEqual(selected.region, "global")
            self.assertEqual(selected.meta_path, global_dec.resolve())
            self.assertEqual(calls, [(global_dat.resolve(), global_meta.resolve(), "Global")])

    def test_installation_detection_reports_missing_game(self):
        with patch("umml_platform.detect_installations", return_value=[]):
            with self.assertRaises(InstallationError):
                detect_preferred_installation("global")

    def test_gamebanana_browse_parses_rich_records(self):
        payload = {
            "_aRecords": [{
                "_idRow": 123,
                "_sName": "Pretty UI",
                "_sVersion": "1.4",
                "_sText": "<b>Dark</b> menus",
                "_aSubmitter": {"_sName": "Modder"},
                "_sProfileUrl": "https://gamebanana.com/mods/123",
                "_nLikeCount": 11,
                "_nDownloadCount": 50,
                "_aFiles": [{"_idRow": 9, "_sFile": "pretty.zip", "_sDownloadUrl": "https://example.test/pretty.zip"}],
            }],
            "_aMetadata": {"_nRecordCount": 1, "_bIsComplete": True},
        }

        def opener(_request, timeout=30):
            return JsonResponse(json.dumps(payload).encode())

        page = GameBananaClient(opener=opener).browse(region="global", query="Pretty")
        self.assertEqual(page.mods[0].name, "Pretty UI")
        self.assertEqual(page.mods[0].description, "Dark menus")
        self.assertEqual(page.mods[0].likes, 11)

    def test_apply_and_restore_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = ManagerStore(root / "manager")
            dat = root / "dat"
            original = dat / "aa" / "aafile"
            original.parent.mkdir(parents=True)
            original.write_text("original")
            prepared = root / "prepared"
            replacement = prepared / "aa" / "aafile"
            replacement.parent.mkdir(parents=True)
            replacement.write_text("modded")
            mod = ModRecord("a", "A", prepared_path=str(prepared), files={"aa/aafile": hash_file(replacement)})
            enabled = resolve_profile(Profile("On", ["a"]), [mod])
            disabled = resolve_profile(Profile("Off", []), [mod])
            engine = ApplyEngine(store, dat, process_check=lambda _: ())
            engine.apply(enabled)
            self.assertEqual(original.read_text(), "modded")
            engine.apply(disabled)
            self.assertEqual(original.read_text(), "original")

    def test_external_change_blocks_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = ManagerStore(root / "manager")
            dat = root / "dat"
            target = dat / "aa" / "aafile"
            target.parent.mkdir(parents=True)
            target.write_text("original")
            prepared = root / "prepared"
            source = prepared / "aa" / "aafile"
            source.parent.mkdir(parents=True)
            source.write_text("modded")
            mod = ModRecord("a", "A", prepared_path=str(prepared), files={"aa/aafile": hash_file(source)})
            engine = ApplyEngine(store, dat, process_check=lambda _: ())
            engine.apply(resolve_profile(Profile("On", ["a"]), [mod]))
            target.write_text("changed elsewhere")
            with self.assertRaises(ApplyError):
                engine.apply(resolve_profile(Profile("Off", []), [mod]))
            self.assertEqual(target.read_text(), "changed elsewhere")


if __name__ == "__main__":
    unittest.main()
