from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .locking import FileLock, LockError
from .process import running_game_processes
from .resolver import Resolution
from .safety import (
    SafetyError,
    atomic_copy_file,
    atomic_write_json,
    hash_file,
    normalize_relative_path,
    path_under,
    validate_sha256,
)
from .store import ManagerStore

ACTIVE_VERSION = 2
JOURNAL_VERSION = 1


class ApplyError(RuntimeError):
    pass


@dataclass(frozen=True)
class ApplyResult:
    installed: int
    restored: int
    unchanged: int
    recovered_transactions: int = 0


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
        self.dat_path = Path(dat_path).expanduser()
        self.game_dir = game_dir
        self.process_check = process_check
        self.target_id = _target_id(self.dat_path)

    def apply(self, resolution: Resolution, *, force: bool = False) -> ApplyResult:
        self._validate_resolution(resolution)
        if not self.dat_path.is_dir():
            raise ApplyError(f"Game dat directory not found: {self.dat_path}")
        try:
            with FileLock(
                self.store.paths.locks / f"deployment-{self.target_id}.lock",
                purpose="applying or recovering a profile",
            ):
                recovered = self._recover_incomplete_transactions()
                self._assert_game_closed()
                self._ensure_baseline_scope()
                active_document = self._read_active_document()
                active = dict(active_document["files"])
                desired = resolution.winners
                affected = sorted(set(active) | set(desired))
                self._validate_sources(desired)
                self._check_external_changes(active, affected, force)
                return self._apply_transaction(
                    resolution,
                    active_document,
                    active,
                    affected,
                    recovered,
                )
        except LockError as exc:
            raise ApplyError(str(exc)) from exc
        except SafetyError as exc:
            raise ApplyError(str(exc)) from exc

    def _validate_resolution(self, resolution: Resolution) -> None:
        groups = (
            ("Missing mods", resolution.missing),
            ("Unprepared mods", resolution.unprepared),
            ("Unsupported packages", resolution.unsupported),
            ("Region incompatibilities", resolution.incompatible),
            ("Invalid manifests", resolution.invalid),
            ("Missing dependencies", resolution.missing_dependencies),
            ("Declared incompatibilities", resolution.incompatibility_conflicts),
        )
        problems = [
            f"{label}: {', '.join(values)}"
            for label, values in groups
            if values
        ]
        if problems:
            raise ApplyError("Profile cannot be applied.\n" + "\n".join(problems))

    def _assert_game_closed(self) -> None:
        running = self.process_check(self.game_dir)
        if running:
            names = ", ".join(
                sorted({getattr(item, "name", "game") for item in running})
            )
            raise ApplyError(
                f"Game is running ({names}); close it before applying changes"
            )

    def _validate_sources(self, desired: dict) -> None:
        failures: list[str] = []
        for relative, claim in desired.items():
            source = path_under(claim.source_path, relative)
            if not source.is_file():
                failures.append(f"{claim.mod_id}: missing {relative}")
                continue
            actual = hash_file(source)
            if actual != claim.sha256:
                failures.append(
                    f"{claim.mod_id}: prepared hash changed for {relative} "
                    f"(expected {claim.sha256}, found {actual})"
                )
        if failures:
            raise ApplyError(
                "Prepared cache verification failed. Re-prepare the affected mods.\n"
                + "\n".join(failures[:20])
            )

    def _apply_transaction(
        self,
        resolution: Resolution,
        active_document: dict,
        active: dict,
        affected: list[str],
        recovered: int,
    ) -> ApplyResult:
        self.store.paths.transactions.mkdir(parents=True, exist_ok=True)
        transaction = Path(
            tempfile.mkdtemp(
                prefix=f"apply-{self.target_id}-",
                dir=self.store.paths.transactions,
            )
        )
        transaction_id = transaction.name
        snapshots = transaction / "snapshots"
        snapshots.mkdir(parents=True, exist_ok=True)
        journal_path = transaction / "journal.json"
        manifest: dict[str, bool] = {}
        active_written = False
        atomic_write_json(
            journal_path,
            self._journal(transaction_id, "snapshotting", manifest),
        )
        try:
            for relative in affected:
                target = path_under(self.dat_path, relative)
                snapshot = path_under(snapshots, relative)
                if target.exists() and not target.is_file():
                    raise ApplyError(f"Managed target is not a regular file: {target}")
                existed = target.is_file()
                manifest[relative] = existed
                if existed:
                    atomic_copy_file(target, snapshot)
            atomic_write_json(
                journal_path,
                self._journal(transaction_id, "applying", manifest),
            )
            self._assert_game_closed()

            installed = restored = unchanged = 0
            new_active: dict[str, dict[str, str]] = {}
            for relative in affected:
                target = path_under(self.dat_path, relative)
                claim = resolution.winners.get(relative)
                if claim is None:
                    if self._restore_baseline(relative, target):
                        restored += 1
                    continue
                source = path_under(claim.source_path, relative)
                if target.is_file() and hash_file(target) == claim.sha256:
                    unchanged += 1
                else:
                    self._capture_baseline(relative, target, active.get(relative))
                    atomic_copy_file(source, target)
                    installed += 1
                new_active[relative] = {
                    "owner": claim.mod_id,
                    "version": claim.mod_version,
                    "sha256": claim.sha256,
                    "profile": resolution.profile,
                }

            self._write_active(new_active, transaction_id=transaction_id)
            active_written = True
            atomic_write_json(
                journal_path,
                self._journal(transaction_id, "committed", manifest),
            )
            shutil.rmtree(transaction, ignore_errors=True)
            return ApplyResult(
                installed=installed,
                restored=restored,
                unchanged=unchanged,
                recovered_transactions=recovered,
            )
        except Exception as exc:
            rollback_error: Exception | None = None
            try:
                self._rollback(snapshots, manifest)
                if active_written:
                    self._write_active_document(active_document)
            except Exception as recovery_exc:
                rollback_error = recovery_exc
            if rollback_error is None:
                shutil.rmtree(transaction, ignore_errors=True)
            if rollback_error is not None:
                raise ApplyError(
                    "Apply failed and automatic rollback also failed. Preserve this recovery "
                    f"directory and do not apply another profile: {transaction}\n"
                    f"Apply error: {exc}\nRollback error: {rollback_error}"
                ) from exc
            if isinstance(exc, ApplyError):
                raise
            raise ApplyError(f"Apply failed and was rolled back: {exc}") from exc

    def _capture_baseline(
        self,
        relative: str,
        target: Path,
        active_record: object,
    ) -> None:
        baseline = path_under(self.store.paths.baseline, relative)
        marker = baseline.with_name(baseline.name + ".umml-missing")
        if baseline.exists() or marker.exists():
            if active_record:
                return
            if (
                baseline.is_file()
                and target.is_file()
                and hash_file(baseline) == hash_file(target)
            ):
                return
            if marker.is_file() and not target.exists():
                return
            raise ApplyError(
                f"The vanilla baseline for {relative} no longer matches the game. "
                "A game update or another tool changed this path. Baseline refresh "
                "must be explicit."
            )
        baseline.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            atomic_copy_file(target, baseline)
        elif target.exists():
            raise ApplyError(f"Cannot capture a non-file baseline: {target}")
        else:
            atomic_write_json(marker, {"version": 1, "missing": True})

    def _restore_baseline(self, relative: str, target: Path) -> bool:
        baseline = path_under(self.store.paths.baseline, relative)
        marker = baseline.with_name(baseline.name + ".umml-missing")
        if baseline.is_file():
            atomic_copy_file(baseline, target)
            return True
        if marker.is_file():
            if target.exists() and not target.is_file():
                raise ApplyError(f"Cannot remove non-file managed target: {target}")
            existed = target.exists()
            target.unlink(missing_ok=True)
            return existed
        raise ApplyError(
            f"No vanilla baseline exists for previously managed path {relative}. "
            "The active state was preserved and no further files were changed."
        )

    def _check_external_changes(
        self,
        active: dict,
        affected: list[str],
        force: bool,
    ) -> None:
        if force:
            return
        conflicts: list[str] = []
        for relative in affected:
            record = active.get(relative)
            if not isinstance(record, dict):
                continue
            target = path_under(self.dat_path, relative)
            expected = str(record["sha256"])
            if not target.is_file() or hash_file(target) != expected:
                conflicts.append(relative)
        if conflicts:
            sample = ", ".join(conflicts[:5])
            raise ApplyError(
                f"{len(conflicts)} active asset(s) changed outside UMML Manager "
                f"({sample}). Refusing to overwrite them without --force."
            )

    def _rollback(self, snapshots: Path, manifest: dict[str, bool]) -> None:
        failures: list[str] = []
        for relative, existed in manifest.items():
            try:
                target = path_under(self.dat_path, relative)
                snapshot = path_under(snapshots, relative)
                if existed:
                    if not snapshot.is_file():
                        raise ApplyError(f"Recovery snapshot is missing: {snapshot}")
                    atomic_copy_file(snapshot, target)
                else:
                    if target.exists() and not target.is_file():
                        raise ApplyError(f"Recovery target is not a file: {target}")
                    target.unlink(missing_ok=True)
            except Exception as exc:
                failures.append(f"{relative}: {exc}")
        if failures:
            raise ApplyError(
                "Rollback could not restore every path:\n"
                + "\n".join(failures[:20])
            )

    def _recover_incomplete_transactions(self) -> int:
        root = self.store.paths.transactions
        if not root.is_dir():
            return 0
        recovered = 0
        for transaction in sorted(root.glob(f"apply-{self.target_id}-*")):
            if not transaction.is_dir():
                continue
            journal_path = transaction / "journal.json"
            try:
                journal = json.loads(journal_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ApplyError(
                    f"Incomplete deployment has an unreadable journal: {transaction}. "
                    "Do not delete it until its snapshots are inspected."
                ) from exc
            if not isinstance(journal, dict) or journal.get("target_id") != self.target_id:
                raise ApplyError(f"Invalid deployment journal: {journal_path}")
            phase = str(journal.get("phase", ""))
            manifest = journal.get("manifest", {})
            if not isinstance(manifest, dict):
                raise ApplyError(
                    f"Invalid deployment snapshot manifest: {journal_path}"
                )
            normalized_manifest = self._validate_snapshot_manifest(manifest, journal_path)

            # Snapshotting cannot have modified the game. It is deliberately
            # cleaned before active-state migration, including old alpha state.
            if phase == "snapshotting":
                shutil.rmtree(transaction, ignore_errors=True)
                recovered += 1
                continue

            active_document = self._read_active_document(allow_legacy=False)
            if active_document.get("transaction_id") == transaction.name:
                shutil.rmtree(transaction, ignore_errors=True)
                recovered += 1
                continue
            if phase in {"applying", "committed"}:
                self._rollback(transaction / "snapshots", normalized_manifest)
                shutil.rmtree(transaction, ignore_errors=True)
                recovered += 1
                continue
            raise ApplyError(
                f"Unknown deployment journal phase {phase!r}: {journal_path}"
            )
        return recovered

    @staticmethod
    def _validate_snapshot_manifest(
        manifest: dict,
        journal_path: Path,
    ) -> dict[str, bool]:
        result: dict[str, bool] = {}
        for relative, existed in manifest.items():
            try:
                canonical = normalize_relative_path(str(relative))
            except SafetyError as exc:
                raise ApplyError(
                    f"Unsafe path in deployment journal {journal_path}: {relative!r}"
                ) from exc
            if canonical in result:
                raise ApplyError(
                    f"Duplicate path in deployment journal {journal_path}: {canonical}"
                )
            result[canonical] = bool(existed)
        return result

    def _read_active_document(self, *, allow_legacy: bool = True) -> dict:
        path = self.store.paths.state
        if not path.is_file():
            return {
                "version": ACTIVE_VERSION,
                "target_id": self.target_id,
                "dat_path": str(self.dat_path.resolve()),
                "files": {},
            }
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ApplyError(
                f"UMML Manager's active deployment state is unreadable: {path}. "
                "No game files were changed. Restore or inspect this file before retrying."
            ) from exc
        if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
            raise ApplyError(
                f"UMML Manager's active deployment state has an invalid format: {path}. "
                "No game files were changed."
            )
        recorded_target = str(data.get("target_id", ""))
        if recorded_target and recorded_target != self.target_id:
            raise ApplyError(
                "The active deployment state belongs to another game installation. "
                f"Recorded target {recorded_target}; current target {self.target_id}."
            )
        if not recorded_target and data["files"]:
            if not allow_legacy or not self._saved_dat_matches():
                raise ApplyError(
                    "Legacy deployment state has no installation identity. Open the "
                    "installation saved when it was created before migrating or recovering it."
                )
            data["target_id"] = self.target_id
            data["dat_path"] = str(self.dat_path.resolve())
        data["files"] = self._validate_active_files(data["files"], path)
        return data

    @staticmethod
    def _validate_active_files(files: dict, state_path: Path) -> dict:
        validated: dict[str, dict[str, str]] = {}
        for relative, raw_record in files.items():
            try:
                canonical = normalize_relative_path(str(relative))
            except SafetyError as exc:
                raise ApplyError(
                    f"Unsafe managed path in active state {state_path}: {relative!r}"
                ) from exc
            if canonical in validated:
                raise ApplyError(
                    f"Duplicate managed path in active state {state_path}: {canonical}"
                )
            if not isinstance(raw_record, dict):
                raise ApplyError(
                    f"Invalid active record for {canonical} in {state_path}"
                )
            try:
                sha256 = validate_sha256(str(raw_record.get("sha256", "")))
            except SafetyError as exc:
                raise ApplyError(
                    f"Invalid active SHA-256 for {canonical} in {state_path}"
                ) from exc
            validated[canonical] = {
                "owner": str(raw_record.get("owner", "")),
                "version": str(raw_record.get("version", "")),
                "sha256": sha256,
                "profile": str(raw_record.get("profile", "")),
            }
        return validated

    def _write_active(self, files: dict, *, transaction_id: str) -> None:
        self._write_active_document(
            {
                "version": ACTIVE_VERSION,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "target_id": self.target_id,
                "dat_path": str(self.dat_path.resolve()),
                "transaction_id": transaction_id,
                "files": files,
            }
        )

    def _write_active_document(self, data: dict) -> None:
        atomic_write_json(self.store.paths.state, data)

    def _ensure_baseline_scope(self) -> None:
        manifest = self.store.paths.baseline / ".umml-target.json"
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ApplyError(
                    f"Baseline target manifest is unreadable: {manifest}"
                ) from exc
            if not isinstance(data, dict) or data.get("target_id") != self.target_id:
                raise ApplyError(
                    "The vanilla baseline belongs to another game installation. "
                    "Do not reuse it across Global/Japan or different Steam libraries."
                )
            return
        has_baseline = self.store.paths.baseline.is_dir() and any(
            path.name != manifest.name
            for path in self.store.paths.baseline.rglob("*")
        )
        if has_baseline and not self._saved_dat_matches():
            raise ApplyError(
                "Legacy vanilla baseline has no installation identity and the saved game "
                "path does not match the current target."
            )
        atomic_write_json(
            manifest,
            {
                "version": 1,
                "target_id": self.target_id,
                "dat_path": str(self.dat_path.resolve()),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def _saved_dat_matches(self) -> bool:
        saved = str(self.store.load_settings().get("dat_path", ""))
        if not saved:
            return False
        try:
            return Path(saved).expanduser().resolve() == self.dat_path.resolve()
        except OSError:
            return False

    def _journal(
        self,
        transaction_id: str,
        phase: str,
        manifest: dict[str, bool],
    ) -> dict:
        return {
            "version": JOURNAL_VERSION,
            "transaction_id": transaction_id,
            "target_id": self.target_id,
            "dat_path": str(self.dat_path.resolve()),
            "phase": phase,
            "manifest": dict(manifest),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


def _target_id(dat_path: Path) -> str:
    try:
        canonical = str(dat_path.resolve())
    except OSError:
        canonical = str(dat_path.absolute())
    return hashlib.sha256(
        canonical.encode("utf-8", errors="surrogateescape")
    ).hexdigest()[:20]
