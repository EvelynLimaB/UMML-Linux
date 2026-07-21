import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseContractTests(unittest.TestCase):
    def test_version_is_release_safe(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?$")

    def test_installer_contains_complete_runtime(self):
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        for name in ("UMML.py", "UMML_core.py", "umml_platform.py", "UMML_data"):
            self.assertIn(name, installer)

    def test_release_builder_includes_runtime_files(self):
        builder = (ROOT / "scripts" / "build_release.sh").read_text(encoding="utf-8")
        for name in ("UMML.py", "UMML_core.py", "umml_platform.py", "install.sh", "VERSION"):
            self.assertIn(name, builder)

    def test_readme_mentions_current_version(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(version, readme)


if __name__ == "__main__":
    unittest.main()
