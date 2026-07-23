from __future__ import annotations

from pathlib import Path

from .models import PACKAGE_UMML_ASSETS
from .process import running_game_processes
from .safety import SafetyError, hash_file, validate_sha256
from .ui_button_actions import ButtonStateActions


class MaintenanceActions(ButtonStateActions):
    """User-facing maintenance status built from verified runtime state."""

    def _mod_status(self, mod) -> str:
        if mod.package_type != PACKAGE_UMML_ASSETS:
            return f"{mod.package_type}; backend needed"
        if not mod.files or not mod.prepared_path:
            return "needs prepare"
        current = self.metadata_fingerprint.get().strip().casefold()
        prepared = str(mod.prepared_against or "").strip().casefold()
        if current and not prepared:
            return "unverified; re-prepare"
        if current and current != prepared:
            return "stale; re-prepare"
        if not current:
            return "prepared; target unverified"
        return "prepared"

    def _manager_diagnostics(self) -> tuple[str, bool]:
        report, ready = super()._manager_diagnostics()
        lines = [report, "", "Target verification:"]

        dat = Path(self.dat_path.get()).expanduser()
        game = Path(self.game_dir.get()).expanduser()
        meta = Path(self.meta_path.get()).expanduser()
        for label, path, expected in (
            ("Game asset data", dat, "directory"),
            ("Game installation", game, "directory"),
            ("Prepared metadata", meta, "file"),
        ):
            exists = path.is_dir() if expected == "directory" else path.is_file()
            lines.append(
                f"{label}: {'READY' if exists else 'CHECK'} ({path or 'not set'})"
            )
            ready = ready and exists

        recorded = self.metadata_fingerprint.get().strip()
        if meta.is_file() and recorded:
            try:
                expected = validate_sha256(recorded)
                actual = hash_file(meta)
            except (OSError, SafetyError) as exc:
                lines.append(f"Metadata integrity: FAILED ({exc})")
                ready = False
            else:
                if actual == expected:
                    lines.append("Metadata integrity: READY")
                else:
                    lines.append(
                        "Metadata integrity: CHECK (saved fingerprint no longer "
                        "matches the prepared metadata file)"
                    )
                    ready = False
        else:
            lines.append("Metadata integrity: CHECK (no verified fingerprint)")
            ready = False

        try:
            running = running_game_processes(self.game_dir.get() or None)
        except Exception as exc:
            lines.append(f"Game process inspection: FAILED ({exc})")
            ready = False
        else:
            state = "game running" if running else "game closed"
            lines.append(f"Game process inspection: READY ({state})")

        return "\n".join(lines), ready
