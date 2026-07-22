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
        self.assertEqual(manager_version(), "0.2.0~alpha5")

    def test_resolver_uses_profile_order_and_reports_conflict(self):
        first = ModRecord(
            "a", "A", prepared_path="/a", files={"aa/aafile": "one"}
        )
        second = ModRecord(
            "b", "B", prepared_path="/b", files={"aa/aafile": "two"}
        )
        result = resolve_profile(Profile("Default", ["a", "b"]), [first, second])
        self.assertEqual(result.winners["aa/aafile"].mod_id, "b")
        self.assertEqual(result.conflicts[0].overridden, ("a",))

    def test_enabled_unprepared_mod_blocks_apply(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dat = root / "dat"
            dat.mkdir()
            store = ManagerStore(root / "manager")
            mod = ModRecord("a", "A")
            resolution = resolve_profile(Profile("Default", ["a"]), [mod])
            self.assertEqual(resolution.unprepared, ["a"])
            with self.assertRaises(ApplyError):
                ApplyEngine(store, dat, process_check=lambda _: ()).apply(resolution)

    def test_archive_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("../escape", "bad")
            with self.assertRaises(StoreError):
                ManagerStore(root / "manager").import_archive(archive)

    def test_archive_expansion_limit_is_enforced_before_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "large.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr(
                    "setting.json",
                    json.dumps({"title": "Large", "mod_version": "1"}),
                )
                package.writestr("assets/file", b"12345678")
            with patch("umml_manager.store.MAX_ARCHIVE_UNCOMPRESSED_BYTES", 4):
                with self.assertRaises(StoreError):
                    ManagerStore(root / "manager").import_archive(archive)
            self.assertFalse((root / "manager" / "sources").exists())

    def test_archive_special_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "link.zip"
            link = zipfile.ZipInfo("assets/link")
            link.create_system = 3
            link.external_attr = 0o120777 << 16
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("setting.json", '{"title":"Link","mod_version":"1"}')
                package.writestr(link, "target")
            with self.assertRaises(StoreError):
                ManagerStore(root / "manager").import_archive(archive)

    def test_nested_mod_folder_is_detected_and_imported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mod = root / "Downloads" / "author-package" / "actual-mod"
            (mod / "assets").mkdir(parents=True)
            (mod / "assets" / "texture.bundle").write_bytes(b"asset")
            (mod / "setting.json").write_text(
                json.dumps({"title": "Detected mod", "mod_version": "2"}),
                encoding="utf-8",
            )
            candidates = scan_mod_candidates([root / "Downloads"])
            self.assertEqual([item.path for item in candidates], [mod])
            record = ManagerStore(root / "manager").import_folder(root / "Downloads")
            self.assertEqual(record.name, "Detected mod")
            self.assertEqual(record.version, "2")

    def test_same_version_cannot_overwrite_immutable_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mod = root / "mod"
            (mod / "assets").mkdir(parents=True)
            (mod / "assets" / "file").write_text("original")
            (mod / "setting.json").write_text(
                '{"title":"Immutable","mod_version":"1"}'
            )
            store = ManagerStore(root / "manager")
            record = store.import_folder(mod)
            (mod / "assets" / "file").write_text("changed")
            with self.assertRaises(StoreError):
                store.import_folder(mod)
            self.assertEqual(
                (Path(record.source_path) / "assets" / "file").read_text(),
                "original",
            )

    def test_different_versions_coexist_under_distinct_record_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = ManagerStore(root / "manager")
            first = root / "first"
            second = root / "second"
            for folder, version, body in (
                (first, "1", "one"),
                (second, "2", "two"),
            ):
                (folder / "assets").mkdir(parents=True)
                (folder / "assets" / "file").write_text(body)
                (folder / "setting.json").write_text(
                    json.dumps({"title": "Same Mod", "mod_version": version})
                )
            old = store.import_folder(first)
            new = store.import_folder(second)
            self.assertNotEqual(old.id, new.id)
            self.assertEqual({item.version for item in store.list_mods()}, {"1", "2"})

    def test_workspace_is_a_copy_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mod = root / "mod"
            (mod / "assets").mkdir(parents=True)
            (mod / "assets" / "file").write_text("original")
            (mod / "setting.json").write_text(
                '{"title":"Editable","mod_version":"1"}'
            )
            store = ManagerStore(root / "manager")
            record = store.import_folder(mod)
            workspace = store.create_workspace(record.id)
            (workspace / "assets" / "file").write_text("edited")
            self.assertEqual(
                (Path(record.source_path) / "assets" / "file").read_text(),
                "original",
            )
            self.assertTrue((workspace / ".umml-workspace.json").is_file())

    def test_corrupt_registry_is_not_silently_reset(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ManagerStore(Path(temp) / "manager")
            store.paths.registry.write_text("{broken")
            with self.assertRaises(StoreError):
                store.list_mods()

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
                selected = detect_preferred_installation(
                    "global", decryptor=decryptor
                )
            self.assertEqual(selected.key, "steam-global")
            self.assertEqual(selected.region, "global")
            self.assertEqual(selected.meta_path, global_dec.resolve())
            self.assertEqual(
                calls,
                [(global_dat.resolve(), global_meta.resolve(), "Global")],
            )

    def test_installation_detection_reports_missing_game(self):
        with patch("umml_platform.detect_installations", return_value=[]):
            with self.assertRaises(InstallationError):
                detect_preferred_installation("global")

    def test_gamebanana_browse_parses_rich_records(self):
        payload = {
            "_aRecords": [
                {
                    "_idRow": 123,
                    "_sName": "Pretty UI",
                    "_sVersion": "1.4",
                    "_sText": "<b>Dark</b> menus",
                    "_aSubmitter": {"_sName": "Modder"},
                    "_sProfileUrl": "https://gamebanana.com/mods/123",
                    "_nLikeCount": 11,
                    "_nDownloadCount": 50,
                    "_aFiles": [
                        {
                            "_idRow": 9,
                            "_sFile": "pretty.zip",
                            "_sDownloadUrl": "https://example.test/pretty.zip",
                        }
                    ],
                }
            ],
            "_aMetadata": {"_nRecordCount": 1, "_bIsComplete": True},
        }

        def opener(_request, timeout=30):
            return JsonResponse(json.dumps(payload).encode())

        page = GameBananaClient(opener=opener).browse(
            region="global", query="Pretty"
        )
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
            mod = ModRecord(
                "a",
                "A",
                prepared_path=str(prepared),
                files={"aa/aafile": hash_file(replacement)},
            )
            enabled = resolve_profile(Profile("On", ["a"]), [mod])
            disabled = resolve_profile(Profile("Off", []), [mod])
            engine = ApplyEngine(store, dat, process_check=lambda _: ())
            engine.apply(enabled)
            self.assertEqual(original.read_text(), "modded")
            engine.apply(disabled)
            self.assertEqual(original.read_text(), "original")

    def test_corrupt_active_state_blocks_apply_before_file_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = ManagerStore(root / "manager")
            dat = root / "dat"
            target = dat / "aa" / "aafile"
            target.parent.mkdir(parents=True)
            target.write_text("original")
            store.paths.state.write_text("{broken")
            with self.assertRaises(ApplyError):
                ApplyEngine(store, dat, process_check=lambda _: ()).apply(
                    resolve_profile(Profile("Off", []), [])
                )
            self.assertEqual(target.read_text(), "original")

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
            mod = ModRecord(
                "a",
                "A",
                prepared_path=str(prepared),
                files={"aa/aafile": hash_file(source)},
            )
            engine = ApplyEngine(store, dat, process_check=lambda _: ())
            engine.apply(resolve_profile(Profile("On", ["a"]), [mod]))
            target.write_text("changed elsewhere")
            with self.assertRaises(ApplyError):
                engine.apply(resolve_profile(Profile("Off", []), [mod]))
            self.assertEqual(target.read_text(), "changed elsewhere")


if __name__ == "__main__":
    unittest.main()
