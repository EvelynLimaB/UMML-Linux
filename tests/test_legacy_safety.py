import unittest
from unittest.mock import patch

import umml_legacy_safety as safety


class LegacySafetyTests(unittest.TestCase):
    def test_recognizes_game_process_name(self):
        process = safety.RunningProcess(12, "umamusume.exe", "C:/game/umamusume.exe")
        self.assertTrue(safety.process_looks_like_game(process))

    def test_rejects_unrelated_process(self):
        process = safety.RunningProcess(12, "python3", "python3 build.py")
        self.assertFalse(safety.process_looks_like_game(process, "/games/umamusume"))

    def test_recognizes_executable_inside_game_directory(self):
        process = safety.RunningProcess(12, "wine64-preloader", "/games/uma/Game.exe")
        self.assertTrue(safety.process_looks_like_game(process, "/games/uma"))

    def test_guard_blocks_mutation_while_game_runs(self):
        calls = []

        class FakeGUI:
            root = None
            game_dir = "/games/uma"

            def load_assets(self):
                calls.append("loaded")
                return "ok"

        safety.install_legacy_safety(FakeGUI)
        running = (safety.RunningProcess(99, "umamusume.exe"),)
        with patch.object(safety, "find_game_processes", return_value=running), patch.object(
            safety, "_warn_game_running"
        ) as warning:
            self.assertIsNone(FakeGUI().load_assets())
        self.assertEqual(calls, [])
        warning.assert_called_once()

    def test_guard_allows_mutation_after_game_closes(self):
        class FakeGUI:
            root = None
            game_dir = "/games/uma"

            def load_assets(self):
                return "ok"

        safety.install_legacy_safety(FakeGUI)
        with patch.object(safety, "find_game_processes", return_value=()):
            self.assertEqual(FakeGUI().load_assets(), "ok")


if __name__ == "__main__":
    unittest.main()
