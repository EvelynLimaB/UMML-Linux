from __future__ import annotations

from dataclasses import dataclass, field

from .models import ModRecord, Profile


@dataclass(frozen=True)
class Claim:
    mod_id: str
    source_path: str
    sha256: str


@dataclass(frozen=True)
class Conflict:
    path: str
    winner: str
    overridden: tuple[str, ...]


@dataclass
class Resolution:
    profile: str
    winners: dict[str, Claim] = field(default_factory=dict)
    conflicts: list[Conflict] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


def resolve_profile(profile: Profile, mods: list[ModRecord]) -> Resolution:
    records = {record.id: record for record in mods}
    claims: dict[str, list[Claim]] = {}
    resolution = Resolution(profile=profile.name)
    for mod_id in profile.enabled:
        record = records.get(mod_id)
        if record is None:
            resolution.missing.append(mod_id)
            continue
        for relative, sha256 in sorted(record.files.items()):
            claims.setdefault(relative, []).append(
                Claim(mod_id=record.id, source_path=record.prepared_path, sha256=sha256)
            )
    for relative, path_claims in claims.items():
        winner = path_claims[-1]
        resolution.winners[relative] = winner
        if len(path_claims) > 1:
            resolution.conflicts.append(
                Conflict(
                    path=relative,
                    winner=winner.mod_id,
                    overridden=tuple(claim.mod_id for claim in path_claims[:-1]),
                )
            )
    resolution.conflicts.sort(key=lambda item: item.path)
    return resolution
