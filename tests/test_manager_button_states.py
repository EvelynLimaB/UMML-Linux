import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    from PIL import Image  # noqa: F401
except ImportError:  # Legacy-only validation intentionally installs no manager deps.
    Image = None

if Image is not None:
    from umml_manager.gui import ManagerGUI
    from umml_manager.models import ModRecord, Profile
    from umml_manager.resolver import Resolution


class FakeVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeWidget:
    def __init__(self, **options):
        self.options = dict(options)

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def cget(self, name):
        return self.options.get(name)


class FakeTree:
    def __init__(self, selected=()):
        self.selected = tuple(selected)

    def selection(self):
        return self.selected


@unittest.skipUnless(Image is not None, "Pillow is a manager-only dependency")
class ManagerButtonStateTests(unittest.TestCase):
    def _app(self, *, selected=True, enabled=True, blockers=False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        meta = root / "meta.db"
        dat = root / "dat"
        game = root / "game"
        meta.write_bytes(b"db")
        dat.mkdir()
        game.mkdir()

        mod = ModRecord(
            "mod-a",
            "Mod A",
            package_type="umml-assets",
            prepared_path=str(root / "prepared"),
            prepared_against="fingerprint",
            files={"aa/hash": "0" * 64},
        )
        profile = Profile("Default", ["mod-a", "mod-b"] if enabled else ["mod-b"])
        app = object.__new__(ManagerGUI)
        app._closing = False
        app._busy = False
        app._game_running = False
        app._gb_install_enabled = True
        app._gb_install_text = "Install"
        app._gb_can_previous = True
        app._gb_can_next = True
        app.meta_path = FakeVar(str(meta))
        app.dat_path = FakeVar(str(dat))
        app.game_dir = FakeVar(str(game))
        app.metadata_fingerprint = FakeVar("fingerprint")
        app.installation_key = FakeVar("steam-global")
        app.region = FakeVar("global")
        app.profile_name = FakeVar("Default")
        app.gb_selected = None
        app.gb_results = {}
        app.local_candidates = {}
        app.profile = lambda: profile
        app.current_resolution = lambda: Resolution(
            profile="Default",
            blocking_issues=["blocked"] if blockers else [],
        )
        app.store = SimpleNamespace(get_mod=lambda mod_id: mod if mod_id == mod.id else None)

        selected_values = (mod.id,) if selected else ()
        library_buttons = {
            name: FakeWidget()
            for name in (
                "new_profile_button",
                "search_button",
                "import_folder_button",
                "import_archive_button",
                "preview_conflicts_button",
                "toggle_button",
                "move_up_button",
                "move_down_button",
                "prepare_button",
                "workspace_button",
                "remove_button",
                "apply_button",
            )
        }
        app.library = SimpleNamespace(
            tree=FakeTree(selected_values),
            selected_id=lambda: selected_values[0] if selected_values else None,
            profile_box=FakeWidget(),
            search_entry=FakeWidget(),
            **library_buttons,
        )

        discover_widgets = {
            name: FakeWidget()
            for name in (
                "gb_region_box",
                "gb_sort_box",
                "gb_query_entry",
                "browse_button",
                "open_gb_button",
                "install_gb_button",
                "prev_button",
                "next_button",
                "scan_roots_entry",
                "add_folder_button",
                "scan_button",
                "open_local_button",
                "import_local_button",
            )
        }
        app.discover = SimpleNamespace(**discover_widgets)
        app.selected_local_candidate = lambda: None

        settings_widgets = {
            name: FakeWidget()
            for name in (
                "autodetect_button",
                "dat_browse_button",
                "meta_browse_button",
                "game_browse_button",
                "save_button",
                "diagnostics_button",
                "open_data_button",
                "open_workspaces_button",
                "region_box",
            )
        }
        app.settings = SimpleNamespace(**settings_widgets)
        app.sidebar_diagnostics_button = FakeWidget()
        app.refresh_plan_button = FakeWidget()
        app.studio = SimpleNamespace(
            tool_buttons={"full": FakeWidget(), "database": FakeWidget()},
            tool_mutating={"full": False, "database": True},
        )
        return app, mod, profile

    def test_no_selection_disables_selection_actions(self):
        app, _mod, _profile = self._app(selected=False)
        app.refresh_action_states()
        self.assertEqual(app.library.toggle_button.options["state"], "disabled")
        self.assertEqual(app.library.prepare_button.options["state"], "disabled")
        self.assertEqual(app.library.workspace_button.options["state"], "disabled")
        self.assertEqual(app.library.remove_button.options["state"], "disabled")

    def test_selected_enabled_mod_gets_contextual_controls(self):
        app, _mod, _profile = self._app(selected=True, enabled=True)
        app.refresh_action_states()
        self.assertEqual(app.library.toggle_button.options["text"], "Disable")
        self.assertEqual(app.library.move_up_button.options["state"], "disabled")
        self.assertEqual(app.library.move_down_button.options["state"], "normal")
        self.assertEqual(app.library.prepare_button.options["text"], "Re-prepare")
        self.assertEqual(app.library.prepare_button.options["state"], "normal")
        self.assertEqual(app.library.apply_button.options["state"], "normal")

    def test_game_running_blocks_apply_and_mutating_studio_only(self):
        app, _mod, _profile = self._app()
        app._game_running = True
        app.refresh_action_states()
        self.assertEqual(app.library.apply_button.options["state"], "disabled")
        self.assertEqual(app.library.apply_button.options["text"], "Close game to apply")
        self.assertEqual(app.studio.tool_buttons["database"].options["state"], "disabled")
        self.assertEqual(app.studio.tool_buttons["database"].options["text"], "Close game first")
        self.assertEqual(app.studio.tool_buttons["full"].options["state"], "normal")

    def test_busy_state_disables_mutating_and_network_actions(self):
        app, mod, _profile = self._app()
        app.gb_selected = SimpleNamespace(id=123)
        app.gb_results = {"123": app.gb_selected}
        app._busy = True
        app.refresh_action_states()
        self.assertEqual(app.library.import_archive_button.options["state"], "disabled")
        self.assertEqual(app.discover.browse_button.options["state"], "disabled")
        self.assertEqual(app.discover.install_gb_button.options["state"], "disabled")
        self.assertEqual(app.settings.autodetect_button.options["state"], "disabled")
        self.assertEqual(app.studio.tool_buttons["database"].options["state"], "disabled")

    def test_gamebanana_and_paging_states_restore_after_task(self):
        app, _mod, _profile = self._app()
        app.gb_selected = SimpleNamespace(id=123)
        app.gb_results = {"123": app.gb_selected}
        app.refresh_action_states()
        self.assertEqual(app.discover.install_gb_button.options["state"], "normal")
        self.assertEqual(app.discover.prev_button.options["state"], "normal")
        self.assertEqual(app.discover.next_button.options["state"], "normal")

    def test_blocked_profile_explains_disabled_apply(self):
        app, _mod, _profile = self._app(blockers=True)
        app.refresh_action_states()
        self.assertEqual(app.library.apply_button.options["state"], "disabled")
        self.assertEqual(app.library.apply_button.options["text"], "Fix blockers to apply")


if __name__ == "__main__":
    unittest.main()
