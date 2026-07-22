import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from umml_manager.engine import ApplyEngine, ApplyError
from umml_manager.models import ModRecord, Profile
from umml_manager.resolver import resolve_profile
from umml_manager.safety import atomic_write_json, hash_file
from umml_manager.store import ManagerStore, StoreError


class RecoveryIntegrityTests(unittest.TestCase):
    def test_future_registry_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ManagerStore(Path(temp) / "manager")
            atomic_write_json(
                store.paths.registry,
                {"version": 999, "mods": []},
            )
            with self.assertRaises(StoreError):
                store.list_mods()

    def test_future_profile_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ManagerStore(Path(temp) / "manager")
            atomic_write_json(
                store.paths.profiles,
                {"version": 999, "profiles": []},
            )
            with self.assertRaises(StoreError):
                store.list_profiles()

    def test_corrupt_settings_are_quarantined_before_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ManagerStore(Path(temp) / "manager")
            store.paths.settings.write_text("{broken", encoding="utf-8")
            settings = store.load_settings()
            self.assertEqual(settings["version"], 1)
            self.assertIn("Original preserved", store.settings_warning)
            preserved = list(
                store.paths.root.glob("settings.json.corrupt-*")
            )
            self.assertEqual(len(preserved), 1)
            self.assertEqual(preserved[0].read_text(encoding="utf-8"), "{broken")

    def test_source_change_during_copy_aborts_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mod = root / "mod"
            (mod / "assets").mkdir(parents=True)
            (mod / "assets" / "file").write_text("original")
            (mod / "setting.json").write_text(
                '{"title":"Moving Target","mod_version":"1"}'
            )
            store = ManagerStore(root / "manager")
            real_copytree = shutil.copytree

            def changed_copytree(source, destination, **kwargs):
                result = real_copytree(source, destination, **kwargs)
                (Path(destination) / "assets" / "file").write_text("changed")
                return result

            with patch("umml_manager.store.shutil.copytree", changed_copytree):
                with self.assertRaises(StoreError):
                    store.import_folder(mod)
            self.assertFalse(store.paths.sources.exists())

    def test_tampered_baseline_blocks_restore_and_keeps_active_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = ManagerStore(root / "manager")
            dat = root / "dat"
            target = dat / "aa" / "aafile"
            target.parent.mkdir(parents=True)
            target.write_text("vanilla")
            store.save_settings({"dat_path": str(dat)})

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
            baseline = store.paths.baseline / "aa" / "aafile"
            baseline.write_text("tampered")

            with self.assertRaises(ApplyError):
                engine.apply(resolve_profile(Profile("Off", []), [mod]))
            self.assertEqual(target.read_text(), "modded")

    def test_tampered_recovery_snapshot_blocks_automatic_rollback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = ManagerStore(root / "manager")
            dat = root / "dat"
            dat.mkdir()
            engine = ApplyEngine(store, dat, process_check=lambda _: ())
            transaction = (
                store.paths.transactions
                / f"apply-{engine.target_id}-tampered"
            )
            snapshot = transaction / "snapshots" / "aa" / "aafile"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text("snapshot")
            atomic_write_json(
                transaction / "journal.json",
                {
                    "version": 2,
                    "transaction_id": transaction.name,
                    "target_id": engine.target_id,
                    "phase": "applying",
                    "manifest": {
                        "aa/aafile": {
                            "existed": True,
                            "sha256": "0" * 64,
                        }
                    },
                },
            )
            with self.assertRaises(ApplyError):
                engine._recover_incomplete_transactions()
            self.assertTrue(transaction.is_dir())

    def test_snapshot_failure_before_mutation_cleans_transaction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = ManagerStore(root / "manager")
            dat = root / "dat"
            target = dat / "aa" / "aafile"
            target.parent.mkdir(parents=True)
            target.write_text("managed")
            engine = ApplyEngine(store, dat, process_check=lambda _: ())
            atomic_write_json(
                store.paths.state,
                {
                    "version": 2,
                    "target_id": engine.target_id,
                    "dat_path": str(dat.resolve()),
                    "files": {
                        "aa/aafile": {
                            "owner": "a",
                            "version": "1",
                            "profile": "On",
                            "sha256": hash_file(target),
                        }
                    },
                },
            )

            with patch(
                "umml_manager.engine.atomic_copy_file",
                side_effect=OSError("disk full"),
            ):
                with self.assertRaises(ApplyError) as raised:
                    engine.apply(resolve_profile(Profile("Off", []), []))
            self.assertIn("before game-file mutation", str(raised.exception))
            self.assertEqual(target.read_text(), "managed")
            remaining = list(
                store.paths.transactions.glob(
                    f"apply-{engine.target_id}-*"
                )
            )
            self.assertEqual(remaining, [])

    def test_future_active_state_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = ManagerStore(root / "manager")
            dat = root / "dat"
            dat.mkdir()
            engine = ApplyEngine(store, dat, process_check=lambda _: ())
            atomic_write_json(
                store.paths.state,
                {
                    "version": 999,
                    "target_id": engine.target_id,
                    "files": {},
                },
            )
            with self.assertRaises(ApplyError):
                engine.apply(resolve_profile(Profile("Off", []), []))


if __name__ == "__main__":
    unittest.main()
