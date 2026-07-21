import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from umml_featured_mods import (
    FeaturedModError,
    FeaturedModManager,
    ModMetadata,
    extract_archive,
    find_mod_root,
)


class FeaturedModTests(unittest.TestCase):
    def test_extract_zip_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("../escape.txt", "nope")
            with self.assertRaises(FeaturedModError):
                extract_archive(archive, root / "out")
            self.assertFalse((root / "escape.txt").exists())

    def test_find_mod_root_prefers_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "plain" / "assets").mkdir(parents=True)
            preferred = root / "nested" / "mod"
            (preferred / "assets").mkdir(parents=True)
            (preferred / "setting.json").write_text("{}", encoding="utf-8")
            self.assertEqual(find_mod_root(root), preferred)

    def test_enable_disable_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dat = root / "dat"
            dat.mkdir()
            state = root / "state"
            cache = root / "cache"
            mod_root = root / "mod"
            (mod_root / "assets").mkdir(parents=True)
            original_hash = "aa" + "0" * 62
            original_target = dat / "aa" / original_hash
            original_target.parent.mkdir()
            original_target.write_bytes(b"original")

            decoded_hash = "bb" + "1" * 62

            def decrypt(_src, dst, **_kwargs):
                out = Path(dst)
                out.mkdir(parents=True, exist_ok=True)
                (out / original_hash).write_bytes(b"dark-original")
                (out / decoded_hash).write_bytes(b"dark-new")
                return 2, 0

            manager = FeaturedModManager(
                dat, decrypt, state_root=state, cache_root=cache
            )
            metadata = ModMetadata(
                title="Test",
                author="Author",
                source_url="https://example.invalid/source",
                license_name="CC BY-NC-ND 4.0",
                license_url="https://example.invalid/license",
                file_id=1,
                file_name="test.zip",
                download_url="https://example.invalid/download",
            )
            archive = root / "test.zip"
            archive.write_bytes(b"archive")

            result = manager.enable(metadata, archive, mod_root)
            self.assertEqual(result.changed, 2)
            self.assertEqual(original_target.read_bytes(), b"dark-original")
            new_target = dat / "bb" / decoded_hash
            self.assertEqual(new_target.read_bytes(), b"dark-new")
            self.assertTrue(manager.is_enabled())

            result = manager.disable()
            self.assertEqual(result.changed, 2)
            self.assertEqual(result.conflicts, ())
            self.assertEqual(original_target.read_bytes(), b"original")
            self.assertFalse(new_target.exists())
            self.assertFalse(manager.is_enabled())

    def test_disable_preserves_a_later_mod_conflict(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dat = root / "dat"
            dat.mkdir()
            mod_root = root / "mod"
            (mod_root / "assets").mkdir(parents=True)
            asset_hash = "cc" + "2" * 62

            def decrypt(_src, dst, **_kwargs):
                out = Path(dst)
                out.mkdir(parents=True, exist_ok=True)
                (out / asset_hash).write_bytes(b"dark")
                return 1, 0

            manager = FeaturedModManager(
                dat,
                decrypt,
                state_root=root / "state",
                cache_root=root / "cache",
            )
            metadata = ModMetadata(
                "Test", "Author", "source", "license", "license-url", 1, "x", "url"
            )
            archive = root / "archive"
            archive.write_bytes(b"archive")
            manager.enable(metadata, archive, mod_root)
            target = dat / "cc" / asset_hash
            target.write_bytes(b"another mod")

            result = manager.disable()
            self.assertEqual(result.changed, 0)
            self.assertEqual(result.conflicts, (f"cc/{asset_hash}",))
            self.assertEqual(target.read_bytes(), b"another mod")
            saved = json.loads(manager.state_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "conflicted")


if __name__ == "__main__":
    unittest.main()
