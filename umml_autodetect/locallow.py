"""Bounded, case-insensitive discovery of Unity LocalLow game data."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

from .model import (
    absolute_no_resolve,
    find_child_casefold,
    resolve_casefold_path,
    safe_is_dir,
    valid_data_dir,
)

# Keep fallback scans deliberately small. A Proton prefix normally has only a
# handful of LocalLow publishers and games, but malformed prefixes should not
# make startup crawl an unbounded tree.
_MAX_PUBLISHERS = 64
_MAX_GAMES_PER_PUBLISHER = 128


def _children(path: Path, limit: int) -> list[Path]:
    try:
        return [entry for entry in path.iterdir() if safe_is_dir(entry)][:limit]
    except OSError:
        return []


def iter_locallow_data_dirs(
    prefix: Path,
    company: str = "Cygames",
    game: str = "umamusume",
) -> Iterator[Path]:
    """Yield valid ``meta`` + ``dat`` directories from a Proton prefix.

    Wine paths are case-insensitive, while their Linux backing filesystem often
    is not. Every fixed component is therefore resolved with case-fold matching.
    The preferred Cygames/game path is checked first, followed by bounded scans
    of sibling game folders and, finally, other LocalLow publisher folders.
    """

    users = resolve_casefold_path(prefix / "drive_c" / "users")
    if not safe_is_dir(users):
        return

    ordered: list[Path] = []
    steamuser = find_child_casefold(users, "steamuser")
    if steamuser is not None:
        ordered.append(steamuser)

    username = os.environ.get("USER") or os.environ.get("USERNAME")
    if username:
        user = find_child_casefold(users, username)
        if user is not None:
            ordered.append(user)

    ordered.extend(_children(users, _MAX_PUBLISHERS))

    seen_users: set[str] = set()
    seen_data: set[str] = set()
    for user in ordered:
        user_key = os.path.normcase(str(absolute_no_resolve(user)))
        if user_key in seen_users:
            continue
        seen_users.add(user_key)

        appdata = find_child_casefold(user, "AppData")
        locallow = find_child_casefold(appdata, "LocalLow") if appdata else None
        if not locallow:
            continue

        preferred_company = find_child_casefold(locallow, company)
        publishers: list[Path] = []
        if preferred_company is not None:
            publishers.append(preferred_company)
        publishers.extend(_children(locallow, _MAX_PUBLISHERS))

        seen_publishers: set[str] = set()
        for publisher in publishers:
            publisher_key = os.path.normcase(str(absolute_no_resolve(publisher)))
            if publisher_key in seen_publishers:
                continue
            seen_publishers.add(publisher_key)

            preferred_game = find_child_casefold(publisher, game)
            game_dirs: list[Path] = []
            if preferred_game is not None:
                game_dirs.append(preferred_game)
            game_dirs.extend(_children(publisher, _MAX_GAMES_PER_PUBLISHER))

            for candidate in game_dirs:
                if not valid_data_dir(candidate):
                    continue
                path = absolute_no_resolve(candidate)
                key = os.path.normcase(str(path))
                if key in seen_data:
                    continue
                seen_data.add(key)
                yield path
