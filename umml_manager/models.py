from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

PACKAGE_UMML_ASSETS = "umml-assets"
PACKAGE_HACHIMI = "hachimi"
PACKAGE_UNKNOWN = "unknown"
SUPPORTED_UPDATE_POLICIES = {"notify", "download", "manual"}


@dataclass(frozen=True)
class SourceSpec:
    provider: str = "local"
    url: str = ""
    submission_id: int | None = None
    file_id: int | None = None
    updated_at: int | None = None
    file_name: str = ""
    sha256: str = ""
    size_bytes: int | None = None
    fetched_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SourceSpec":
        data = data or {}
        return cls(
            provider=str(data.get("provider", "local")),
            url=str(data.get("url", "")),
            submission_id=_optional_int(data.get("submission_id")),
            file_id=_optional_int(data.get("file_id")),
            updated_at=_optional_int(data.get("updated_at")),
            file_name=str(data.get("file_name", "")),
            sha256=str(data.get("sha256", "")),
            size_bytes=_optional_int(data.get("size_bytes")),
            fetched_at=str(data.get("fetched_at", "")),
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
    package_type: str = PACKAGE_UMML_ASSETS
    capabilities: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    incompatibilities: list[str] = field(default_factory=list)
    prepared_against: str = ""
    prepared_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModRecord":
        if not isinstance(data, dict):
            raise ValueError("Mod record must be an object")
        if "id" not in data:
            raise ValueError("Mod record is missing id")
        update_policy = str(data.get("update_policy", "notify"))
        if update_policy not in SUPPORTED_UPDATE_POLICIES:
            update_policy = "notify"
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or data["id"]),
            version=str(data.get("version", "0")),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            regions=_string_list(data.get("regions", [])),
            source=SourceSpec.from_dict(data.get("source")),
            source_path=str(data.get("source_path", "")),
            prepared_path=str(data.get("prepared_path", "")),
            files={str(key): str(value) for key, value in _mapping(data.get("files", {})).items()},
            imported_at=str(data.get("imported_at", "")),
            update_policy=update_policy,
            package_type=str(data.get("package_type", PACKAGE_UMML_ASSETS)),
            capabilities=_string_list(data.get("capabilities", [])),
            dependencies=_string_list(data.get("dependencies", [])),
            incompatibilities=_string_list(data.get("incompatibilities", [])),
            prepared_against=str(data.get("prepared_against", "")),
            prepared_at=str(data.get("prepared_at", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Profile:
    name: str
    enabled: list[str] = field(default_factory=list)
    region: str = ""
    installation_key: str = ""
    options: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Profile":
        if not isinstance(data, dict):
            raise ValueError("Profile must be an object")
        if "name" not in data:
            raise ValueError("Profile is missing name")
        raw_options = _mapping(data.get("options", {}))
        options: dict[str, dict[str, Any]] = {}
        for key, value in raw_options.items():
            if isinstance(value, dict):
                options[str(key)] = dict(value)
        return cls(
            name=str(data["name"]),
            enabled=_string_list(data.get("enabled", [])),
            region=str(data.get("region", "")),
            installation_key=str(data.get("installation_key", "")),
            options=options,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "enabled": list(self.enabled),
            "region": self.region,
            "installation_key": self.installation_key,
            "options": {key: dict(value) for key, value in self.options.items()},
        }


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    return [str(item) for item in value]


def _mapping(value: object) -> dict[Any, Any]:
    return dict(value) if isinstance(value, dict) else {}
