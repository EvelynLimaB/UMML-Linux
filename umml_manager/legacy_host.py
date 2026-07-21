from __future__ import annotations

import argparse
import functools
import os
import tkinter as tk
from tkinter import messagebox

from .process import running_game_processes

_MUTATING_METHODS = {
    "load_assets", "load_assets_manual", "restore_original_assets", "unload_assets",
    "clean_unused_assets", "delete_master_db", "force_translate_english",
    "open_chara_settings", "open_personality_settings", "open_dress_settings",
    "open_training_settings", "open_story_concert", "open_swap_character",
}


def _install_guard(cls) -> None:
    for name in _MUTATING_METHODS:
        original = getattr(cls, name, None)
        if original is None or getattr(original, "_umml_manager_guarded", False):
            continue

        @functools.wraps(original)
        def guarded(self, *args, __original=original, __name=name, **kwargs):
            game_dir = getattr(self, "game_dir", "") or os.environ.get("UMML_GAME_DIR", "")
            running = running_game_processes(game_dir or None)
            if running:
                names = ", ".join(sorted({item.name for item in running}))
                messagebox.showwarning(
                    "Close the game first",
                    f"{__name.replace('_', ' ').title()} can change game data.\n\n"
                    f"Detected running process: {names}\n\nClose Umamusume and try again.",
                    parent=getattr(self, "root", None),
                )
                return None
            return __original(self, *args, **kwargs)

        guarded._umml_manager_guarded = True  # type: ignore[attr-defined]
        setattr(cls, name, guarded)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UMML Manager legacy-tool compatibility host")
    parser.add_argument("--tool", default="")
    args = parser.parse_args(argv)

    import UMML as application

    _install_guard(application.ModLoaderGUI)
    root = tk.Tk()
    gui = application.ModLoaderGUI(root)
    root.title("UMML Studio — Legacy compatibility tools")

    if args.tool:
        method = getattr(gui, args.tool, None)
        if not callable(method):
            messagebox.showerror("Tool unavailable", f"Legacy tool is unavailable: {args.tool}", parent=root)
        else:
            root.after(150, method)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
