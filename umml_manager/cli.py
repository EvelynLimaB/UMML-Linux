from __future__ import annotations

import argparse
import json
from pathlib import Path

from .deployment import ApplyEngine
from .discovery import default_search_roots, scan_mod_candidates
from .legacy_adapter import LegacyAssetAdapter
from .models import Profile
from .providers.gamebanana_previews import PreviewGameBananaClient
from .resolver import Resolution, resolve_profile
from .safety import SafetyError, hash_file, validate_sha256
from .store import ManagerStore, StoreError, default_root
from .studio import LegacyToolLauncher
from .version import manager_version

REGIONS = ("global", "japan", "taiwan", "korea")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="umml-manager-cli")
    parser.add_argument(
        "--version",
        action="version",
        version=manager_version(),
    )
    parser.add_argument(
        "--root",
        default=str(default_root()),
        help="Manager data directory",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")

    imported = sub.add_parser("import")
    imported.add_argument("path")
    imported.add_argument("--id")

    scan = sub.add_parser("scan")
    scan.add_argument("paths", nargs="*")
    scan.add_argument("--depth", type=int, default=5)

    browse = sub.add_parser("browse")
    browse.add_argument(
        "--region",
        choices=("global", "japan"),
        default="global",
    )
    browse.add_argument("--page", type=int, default=1)
    browse.add_argument(
        "--sort",
        choices=("updated", "newest", "popular", "downloads", "views"),
        default="updated",
    )
    browse.add_argument("--query", default="")

    gamebanana = sub.add_parser("gamebanana")
    gamebanana.add_argument("url")
    gamebanana.add_argument("--file-id", type=int)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("mod_id")
    prepare.add_argument("--meta", required=True)

    workspace = sub.add_parser("workspace")
    workspace.add_argument("mod_id")

    profile = sub.add_parser("profile")
    profile.add_argument("name")
    profile.add_argument("mods", nargs="*")
    profile.add_argument("--region", choices=REGIONS, default="")
    profile.add_argument("--installation-key", default="")

    plan = sub.add_parser("plan")
    plan.add_argument("profile")
    _add_target_options(plan, dat_required=False)

    apply_command = sub.add_parser("apply")
    apply_command.add_argument("profile")
    _add_target_options(apply_command, dat_required=True)
    apply_command.add_argument("--game-dir")
    apply_command.add_argument("--force", action="store_true")

    updates = sub.add_parser("updates")
    updates.add_argument("mod_id", nargs="?")

    studio = sub.add_parser("studio")
    studio.add_argument("tool", nargs="?", default="full")
    studio.add_argument("--dat", default="")
    studio.add_argument("--game-dir", default="")
    studio.add_argument("--meta", default="")
    studio.add_argument("--region", default="global")
    return parser


def _add_target_options(
    parser: argparse.ArgumentParser,
    *,
    dat_required: bool,
) -> None:
    parser.add_argument("--region", choices=REGIONS, default="")
    parser.add_argument("--installation-key", default="")
    parser.add_argument(
        "--meta",
        default="",
        help=(
            "Prepared metadata DB used to reject stale prepared caches. "
            "Apply requires this path or a valid auto-detected saved metadata path."
        ),
    )
    if dat_required:
        parser.add_argument("--dat", required=True)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = ManagerStore(args.root)
    try:
        if args.command == "list":
            for mod in store.list_mods():
                status = (
                    "prepared"
                    if mod.files and mod.prepared_path
                    else "needs prepare"
                )
                print(
                    f"{mod.id}\t{mod.version}\t{mod.package_type}\t"
                    f"{status}\t{mod.name}"
                )
        elif args.command == "import":
            path = Path(args.path)
            record = (
                store.import_folder(path, mod_id=args.id)
                if path.is_dir()
                else store.import_archive(path, mod_id=args.id)
            )
            print(record.id)
        elif args.command == "scan":
            roots = [Path(item) for item in args.paths] or default_search_roots()
            for candidate in scan_mod_candidates(
                roots,
                max_depth=args.depth,
            ):
                print(
                    f"{candidate.kind}\t{candidate.confidence}\t"
                    f"{candidate.path}\t{candidate.reason}"
                )
        elif args.command == "browse":
            page = PreviewGameBananaClient().browse(
                region=args.region,
                page=args.page,
                sort=args.sort,
                query=args.query,
            )
            for mod in page.mods:
                print(
                    f"{mod.id}\t{mod.likes}\t{mod.downloads}\t"
                    f"{mod.author}\t{mod.name}"
                )
        elif args.command == "gamebanana":
            record = PreviewGameBananaClient().import_mod(
                store,
                args.url,
                file_id=args.file_id,
            )
            print(record.id)
        elif args.command == "prepare":
            record = LegacyAssetAdapter(store, args.meta).prepare(
                store.get_mod(args.mod_id)
            )
            print(f"Prepared {len(record.files)} assets for {record.id}")
        elif args.command == "workspace":
            print(store.create_workspace(args.mod_id))
        elif args.command == "profile":
            store.save_profile(
                Profile(
                    args.name,
                    list(args.mods),
                    region=args.region,
                    installation_key=args.installation_key,
                )
            )
            print(args.name)
        elif args.command in {"plan", "apply"}:
            profile = store.get_profile(args.profile)
            required = args.command == "apply"
            fingerprint = _metadata_fingerprint(
                args.meta,
                store=store,
                required=required,
            )
            target_key = _target_installation_key(
                args.installation_key,
                store=store,
                dat_path=args.dat if required else "",
            )
            resolution = resolve_profile(
                profile,
                store.list_mods(),
                target_region=args.region or profile.region,
                target_installation_key=target_key,
                metadata_fingerprint=fingerprint,
            )
            if args.command == "plan":
                print(json.dumps(_resolution_dict(resolution), indent=2))
            else:
                result = ApplyEngine(
                    store,
                    args.dat,
                    game_dir=args.game_dir,
                ).apply(
                    resolution,
                    force=args.force,
                )
                print(
                    f"Installed {result.installed}; restored "
                    f"{result.restored}; unchanged {result.unchanged}; "
                    f"recovered {result.recovered_transactions} interrupted "
                    "transaction(s)"
                )
        elif args.command == "updates":
            provider = PreviewGameBananaClient()
            records = (
                [store.get_mod(args.mod_id)]
                if args.mod_id
                else store.list_mods()
            )
            for record in records:
                update = provider.update_available(record)
                if update:
                    print(f"{record.id}\t{update.id}\t{update.name}")
        elif args.command == "studio":
            LegacyToolLauncher().launch(
                args.tool,
                dat_path=args.dat,
                game_dir=args.game_dir,
                meta_path=args.meta,
                region=args.region,
            )
        return 0
    except StoreError as exc:
        print(f"error: {exc}")
        return 2
    except Exception as exc:
        print(f"error: {exc}")
        return 1


def _metadata_fingerprint(
    value: str,
    *,
    store: ManagerStore | None = None,
    required: bool = False,
) -> str:
    if value:
        path = Path(value).expanduser()
        if not path.is_file():
            raise StoreError(f"Metadata database not found: {path}")
        return hash_file(path)

    settings = store.load_settings() if store is not None else {}
    saved_meta = str(settings.get("meta_path", "")).strip()
    saved_path = Path(saved_meta).expanduser() if saved_meta else None
    if saved_path is not None and saved_path.is_file():
        actual = hash_file(saved_path)
        recorded = str(settings.get("metadata_fingerprint", "")).strip()
        if recorded:
            try:
                expected = validate_sha256(recorded)
            except SafetyError as exc:
                raise StoreError(
                    "Saved metadata fingerprint is invalid; run installation "
                    "auto-detection again"
                ) from exc
            if actual != expected:
                raise StoreError(
                    "Saved metadata changed since installation detection; run "
                    "auto-detection and re-prepare affected mods"
                )
        return actual

    if required:
        raise StoreError(
            "Apply requires --meta or a valid auto-detected metadata database in "
            "manager settings"
        )
    return ""


def _target_installation_key(
    value: str,
    *,
    store: ManagerStore,
    dat_path: str = "",
) -> str:
    explicit = str(value or "").strip()
    if explicit:
        return explicit
    settings = store.load_settings()
    saved_key = str(settings.get("installation_key", "")).strip()
    if not saved_key:
        return ""
    if not dat_path:
        return saved_key
    saved_dat = str(settings.get("dat_path", "")).strip()
    if not saved_dat:
        return ""
    try:
        matches = (
            Path(saved_dat).expanduser().resolve()
            == Path(dat_path).expanduser().resolve()
        )
    except (OSError, ValueError):
        matches = False
    return saved_key if matches else ""


def _resolution_dict(resolution: Resolution) -> dict:
    return {
        "profile": resolution.profile,
        "target_region": resolution.target_region,
        "target_installation_key": resolution.target_installation_key,
        "metadata_fingerprint": resolution.metadata_fingerprint,
        "files": len(resolution.winners),
        "blocking": resolution.blocking_issues,
        "missing": resolution.missing,
        "unprepared": resolution.unprepared,
        "stale_prepared": resolution.stale_prepared,
        "unsupported": resolution.unsupported,
        "incompatible": resolution.incompatible,
        "wrong_installation": resolution.wrong_installation,
        "invalid": resolution.invalid,
        "missing_dependencies": resolution.missing_dependencies,
        "incompatibility_conflicts": resolution.incompatibility_conflicts,
        "duplicates": resolution.duplicates,
        "conflicts": [
            conflict.__dict__ for conflict in resolution.conflicts
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
