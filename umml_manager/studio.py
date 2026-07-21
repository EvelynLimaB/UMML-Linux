from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LegacyTool:
    id: str
    name: str
    description: str
    method: str | None = None
    mutating: bool = True


LEGACY_TOOLS: tuple[LegacyTool, ...] = (
    LegacyTool("full", "Full legacy workspace", "Every original loader action and editor in one compatibility window.", None, False),
    LegacyTool("attributes", "Character attributes", "Edit character body and presentation attributes.", "open_chara_settings"),
    LegacyTool("personality", "Character personality", "Edit personality and character behavior data.", "open_personality_settings"),
    LegacyTool("dress", "Dress editor", "Inspect and edit dress assignments and colors.", "open_dress_settings"),
    LegacyTool("training", "Training editor", "Edit Single Mode training data.", "open_training_settings"),
    LegacyTool("concert", "Story & concert", "Add, edit, and restore story concert setups.", "open_story_concert"),
    LegacyTool("swap", "Character / model swap", "Swap body, head, tail, attributes, and chibi components.", "open_swap_character"),
    LegacyTool("translation", "Translation merge", "Merge Global text into the Japanese client.", "force_translate_english"),
    LegacyTool("cleanup", "Clean unused assets", "Run the original unused-asset cleanup tool.", "clean_unused_assets"),
    LegacyTool("database", "Database reset", "Delete master.mdb so the game downloads a clean copy.", "delete_master_db"),
)


class LegacyToolLauncher:
    def launch(
        self,
        tool_id: str = "full",
        *,
        dat_path: str = "",
        game_dir: str = "",
        meta_path: str = "",
        region: str = "",
    ) -> subprocess.Popen:
        tool = next((item for item in LEGACY_TOOLS if item.id == tool_id), None)
        if tool is None:
            raise ValueError(f"Unknown legacy tool: {tool_id}")
        env = os.environ.copy()
        dat = Path(dat_path).expanduser() if dat_path else None
        if dat:
            persistent = dat.parent if dat.name.casefold() == "dat" else dat
            env["UMML_PERSISTENT_DIR"] = str(persistent)
        if game_dir:
            env["UMML_GAME_DIR"] = str(Path(game_dir).expanduser())
        if meta_path:
            env["UMML_MANAGER_META_PATH"] = str(Path(meta_path).expanduser())
        if region:
            env["UMML_MANAGER_REGION"] = region
        if getattr(sys, "frozen", False):
            command = [sys.executable, "--legacy-host"]
        else:
            command = [sys.executable, "-m", "umml_manager.legacy_host"]
        if tool.method:
            command += ["--tool", tool.method]
        return subprocess.Popen(command, env=env)


def open_path(path: str | Path) -> None:
    target = str(Path(path).expanduser())
    if sys.platform.startswith("win"):
        os.startfile(target)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])
