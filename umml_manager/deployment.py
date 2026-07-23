from __future__ import annotations

from .engine import ApplyEngine as _TransactionalApplyEngine
from .engine import ApplyError, ApplyResult
from .resolver import Resolution


class ApplyEngine(_TransactionalApplyEngine):
    """Public deployment engine with complete resolver and process guards.

    The transactional implementation remains isolated in ``engine.py``. Every
    supported GUI, CLI, and package-level entry point imports this class so a
    caller cannot accidentally ignore blocker categories added by the planner.
    """

    def _validate_resolution(self, resolution: Resolution) -> None:
        groups = (
            ("Missing mods", resolution.missing),
            ("Unprepared mods", resolution.unprepared),
            ("Stale prepared caches", resolution.stale_prepared),
            ("Unsupported packages", resolution.unsupported),
            ("Region incompatibilities", resolution.incompatible),
            ("Wrong installation", resolution.wrong_installation),
            ("Invalid manifests", resolution.invalid),
            ("Missing dependencies", resolution.missing_dependencies),
            (
                "Declared incompatibilities",
                resolution.incompatibility_conflicts,
            ),
        )
        problems = [
            f"{label}: {', '.join(values)}"
            for label, values in groups
            if values
        ]
        if problems:
            raise ApplyError(
                "Profile cannot be applied.\n" + "\n".join(problems)
            )

    def _assert_game_closed(self) -> None:
        try:
            running = self.process_check(self.game_dir)
        except Exception as exc:
            raise ApplyError(
                "Could not verify whether Umamusume is running. Game-file writes "
                f"were blocked: {exc}"
            ) from exc
        if running:
            names = ", ".join(
                sorted({getattr(item, "name", "game") for item in running})
            )
            raise ApplyError(
                f"Game is running ({names}); close it before applying changes"
            )


__all__ = ["ApplyEngine", "ApplyError", "ApplyResult"]
