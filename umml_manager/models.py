from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceSpec:
    provider: str = "local"
    url: str = ""
    submission_id: int | None = None
    file_id: int | None = None
    updated_at: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SourceSpec":
        data = data or {}
        return cls(
            provider=str(data.get("provider", "local")),
            url=str(data.get("url", "")),
            submission_id=_optional_int(data.get("submission_id")),
            file_id=_optional_int(data.get("file_id")),
            updated_at=_optional_int(data.get("updated_at")),
        )


@dataclass
class ModRecord:
    id: str
    name: str
    version: str = "0"
    description: str = ""
    author: str = ""
    regions: list[str] = field(default_factory=list)
    source: SourceSpec = field(default_factory=SourceSpec)
    source_path: str = ""
    prepared_path: str = ""
    files: dict[str, str] = field(default_factory=dict)
    imported_at: str = ""
    update_policy: str = "notify"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModRecord":
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or data["id"]),
            version=str(data.get("version", "0")),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            regions=[str(value) for value in data.get("regions", [])],
            source=SourceSpec.from_dict(data.get("source")),
            source_path=str(data.get("source_path", "")),
            prepared_path=str(data.get("prepared_path", "")),
            files={str(k): str(v) for k, v in dict(data.get("files", {})).items()},
            imported_at=str(data.get("imported_at", "")),
            update_policy=str(data.get("update_policy", "notify")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Profile:
    name: str
    enabled: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Profile":
        return cls(name=str(data["name"]), enabled=[str(value) for value in data.get("enabled", [])])

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "enabled": list(self.enabled)}


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
