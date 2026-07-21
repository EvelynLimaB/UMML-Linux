from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .process import running_game_processes
from .resolver import Resolution
from .store import ManagerStore, hash_file


class ApplyError(RuntimeError):
    pass


@dataclass(frozen=True)
class ApplyResult:
    installed: int
    restored: int
    unchanged: int


class ApplyEngine:
    def __init__(
        self,
        store: ManagerStore,
        dat_path: str | Path,
        *,
        game_dir: str | Path | None = None,
        process_check: Callable[[str | Path | None], tuple] = running_game_processes,
    ):
        self.store = store
        self.dat_path = Path(dat_path)
        self.game_dir = game_dir
        self.process_check = process_check

    def apply(self, resolution: Resolution, *, force: bool = False) -> ApplyResult:
        if resolution.missing:
            raise ApplyError("Profile references missing mods: " + ", ".join(resolution.missing))
        running = self.process_check(self.game_dir)
        if running:
            names = ", ".join(sorted({getattr(item, "name", "game") for item in running}))
            raise ApplyError(f"Game is running ({names}); changes remain pending until it closes")
        if not self.dat_path.is_dir():
            raise ApplyError(f"Game dat directory not found: {self.dat_path}")
        active = self._read_active()
        desired = resolution.winners
        affected = sorted(set(active) | set(desired))
        self._check_external_changes(active, affected, force)
        self.store.paths.transactions.mkdir(parents=True, exist_ok=True)
        transaction = Path(tempfile.mkdtemp(prefix="apply-", dir=self.store.paths.transactions))
        snapshots = transaction / "snapshots"
        snapshots.mkdir(parents=True, exist_ok=True)
        snapshot_manifest: dict[str, bool] = {}
        try:
            for relative in affected:
                target = self.dat_path / relative
                snapshot = snapshots / relative
                existed = target.is_file()
                snapshot_manifest[relative] = existed
                if existed:
                    snapshot.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, snapshot)
            installed = restored = unchanged = 0
            new_active: dict[str, dict[str, str]] = {}
            for relative in affected:
                target = self.dat_path / relative
                claim = desired.get(relative)
                if claim is None:
                    if self._restore_baseline(relative, target):
                        restored += 1
                    continue
                source = Path(claim.source_path) / relative
                if not source.is_file():
                    raise ApplyError(f"Prepared asset missing for {claim.mod_id}: {source}")
                if target.is_file() and hash_file(target) == claim.sha256:
                    unchanged += 1
                else:
                    self._capture_baseline(relative, target)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    installed += 1
                new_active[relative] = {
                    "owner": claim.mod_id,
                    "sha256": claim.sha256,
                    "profile": resolution.profile,
                }
            self._write_active(new_active)
            shutil.rmtree(transaction, ignore_errors=True)
            return ApplyResult(installed=installed, restored=restored, unchanged=unchanged)
        except Exception as exc:
            self._rollback(snapshots, snapshot_manifest)
            shutil.rmtree(transaction, ignore_errors=True)
            if isinstance(exc, ApplyError):
                raise
            raise ApplyError(f"Apply failed and was rolled back: {exc}") from exc

    def _capture_baseline(self, relative: str, target: Path) -> None:
        baseline = self.store.paths.baseline / relative
        marker = baseline.with_suffix(baseline.suffix + ".missing")
        if baseline.exists() or marker.exists():
            return
        baseline.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            shutil.copy2(target, baseline)
        else:
            marker.touch()

    def _restore_baseline(self, relative: str, target: Path) -> bool:
        baseline = self.store.paths.baseline / relative
        marker = baseline.with_suffix(baseline.suffix + ".missing")
        if baseline.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(baseline, target)
            return True
        if marker.exists():
            existed = target.exists()
            target.unlink(missing_ok=True)
            return existed
        return False

    def _check_external_changes(self, active: dict, affected: list[str], force: bool) -> None:
        if force:
            return
        conflicts: list[str] = []
        for relative in affected:
            record = active.get(relative)
            if not record:
                continue
            target = self.dat_path / relative
            expected = str(record.get("sha256", ""))
            if not target.is_file() or not expected or hash_file(target) != expected:
                conflicts.append(relative)
        if conflicts:
            sample = ", ".join(conflicts[:5])
            raise ApplyError(
                f"{len(conflicts)} active asset(s) changed outside UMML Manager ({sample}). "
                "Refusing to overwrite them without --force."
            )

    def _rollback(self, snapshots: Path, manifest: dict[str, bool]) -> None:
        for relative, existed in manifest.items():
            target = self.dat_path / relative
            snapshot = snapshots / relative
            if existed and snapshot.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(snapshot, target)
            elif not existed:
                target.unlink(missing_ok=True)

    def _read_active(self) -> dict:
        path = self.store.paths.state
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return dict(data.get("files", {}))
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_active(self, files: dict) -> None:
        path = self.store.paths.state
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                {"version": 1, "updated_at": datetime.now(timezone.utc).isoformat(), "files": files},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        os.replace(temp, path)
