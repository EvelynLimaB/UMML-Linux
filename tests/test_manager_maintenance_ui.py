import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from umml_manager.models import ModRecord, Profile
from umml_manager.resolver import Resolution
from umml_manager.ui_maintenance_actions import MaintenanceActions


class FakeVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value


class FakeButton:
    def __init__(self):
        self.options = {}

    def configure(self, **options):
        self.options.update(options)


class MaintenanceUiTests(unittest.TestCase):
    def test_enabled_profile_requires_verified_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            dat = Path(temp) / "dat"
            dat.mkdir()

            class Base:
                @staticmethod
                def _configure_button(widget, *, enabled, text=None):
                    options = {"state": "normal" if enabled else "disabled"}
                    if text is not None:
                        options["text"] = text
                    widget.configure(**options)

                def refresh_action_states(self):
                    self.library.apply_button.configure(
                        state="normal",
                        text="Apply profile",
                    )

                def profile(self):
                    return Profile("Default", ["mod"])

                def current_resolution(self):
                    return Resolution(profile="Default")

            class Harness(MaintenanceActions, Base):
                pass

            harness = Harness()
            harness._closing = False
            harness._busy = False
            harness._game_running = False
            harness.metadata_fingerprint = FakeVar("")
            harness.dat_path = FakeVar(str(dat))
            harness.library = SimpleNamespace(apply_button=FakeButton())

            harness.refresh_action_states()

            self.assertEqual(
                harness.library.apply_button.options["state"],
                "disabled",
            )
            self.assertEqual(
                harness.library.apply_button.options["text"],
                "Verify metadata to apply",
            )

    def test_prepared_cache_without_target_fingerprint_is_visible(self):
        class Harness(MaintenanceActions):
            pass

        harness = Harness()
        harness.metadata_fingerprint = FakeVar("")
        status = harness._mod_status(
            ModRecord(
                "mod",
                "Mod",
                prepared_path="/prepared",
                files={"aa/hash": "1" * 64},
            )
        )
        self.assertEqual(status, "prepared; target unverified")


if __name__ == "__main__":
    unittest.main()
