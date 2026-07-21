import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseContractTests(unittest.TestCase):
    def test_version_is_release_safe(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?$")

    def test_single_autodetection_engine_is_packaged(self):
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        builder = (ROOT / "scripts" / "build_release.sh").read_text(encoding="utf-8")
        entry = (ROOT / "umml_packaged.py").read_text(encoding="utf-8")
        for text in (installer, builder, entry):
            self.assertIn("umml_autodetect", text)
        self.assertFalse((ROOT / "umml_detection_hotfix.py").exists())
        self.assertFalse((ROOT / "umml_manual_location_fix.py").exists())

    def test_installer_contains_complete_runtime(self):
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        for name in ("UMML.py", "UMML_core.py", "umml_platform.py", "sitecustomize.py", "UMML_data"):
            self.assertIn(name, installer)

    def test_source_release_includes_packaging_and_reference_files(self):
        builder = (ROOT / "scripts" / "build_release.sh").read_text(encoding="utf-8")
        for name in (
            "UMML.py", "UMML_core.py", "umml_packaged.py", "umml_platform.py",
            "umml_autodetect", "AUTODETECTION.md", "install.sh", "VERSION",
            "requirements-build.txt", "build_deb.sh", "build_appimage.sh", "umml.spec",
        ):
            self.assertIn(name, builder)

    def test_binary_package_definitions_exist(self):
        expected = (
            "requirements-build.txt",
            "packaging/pyinstaller/umml.spec",
            "packaging/linux/io.github.evelynlimab.umml.desktop",
            "packaging/linux/io.github.evelynlimab.umml.metainfo.xml",
            "scripts/build_frozen.sh",
            "scripts/build_deb.sh",
            "scripts/build_appimage.sh",
        )
        for relative in expected:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_packaged_entry_point_applies_autodetection(self):
        entry = (ROOT / "umml_packaged.py").read_text(encoding="utf-8")
        self.assertIn("_MEIPASS", entry)
        self.assertIn('"--version"', entry)
        self.assertIn("apply_autodetect", entry)

    def test_release_workflow_exercises_real_layouts(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        for name in (
            "build_frozen.sh", "build_deb.sh", "build_appimage.sh",
            "compatdata/3224770", "libraryfolders.vdf", "Steam Global: Detected",
            "result: READY",
        ):
            self.assertIn(name, workflow)
        self.assertIn("*.deb", workflow)
        self.assertIn("*.AppImage", workflow)

    def test_readme_and_appstream_mention_current_version(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        metainfo = (ROOT / "packaging/linux/io.github.evelynlimab.umml.metainfo.xml").read_text(encoding="utf-8")
        self.assertIn(version, readme)
        self.assertIn(version, metainfo)


if __name__ == "__main__":
    unittest.main()
