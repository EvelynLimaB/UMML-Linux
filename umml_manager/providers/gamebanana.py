from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from ..models import SourceSpec
from ..store import ManagerStore, StoreError

GAME_IDS = {"global": 22548, "japan": 22547}


@dataclass(frozen=True)
class GameBananaFile:
    id: int
    name: str
    url: str
    date_added: int = 0
    downloads: int = 0


@dataclass(frozen=True)
class GameBananaMod:
    id: int
    name: str
    author: str
    profile_url: str
    files: tuple[GameBananaFile, ...]
    description: str = ""
    version: str = ""
    date_added: int = 0
    date_updated: int = 0
    views: int = 0
    likes: int = 0
    downloads: int = 0
    image_url: str = ""
    category: str = ""
    game_name: str = ""
    obsolete: bool = False


@dataclass(frozen=True)
class GameBananaPage:
    mods: tuple[GameBananaMod, ...]
    page: int
    total: int = 0
    has_more: bool = False


class GameBananaClient:
    USER_AGENT = "UMML-Manager/0.2 (+https://github.com/EvelynLimaB/UMML-Linux)"
    DETAIL_PROPERTIES = (
        "_idRow,_sName,_aSubmitter,_aFiles,_sProfileUrl,_sVersion,_sText,"
        "_tsDateAdded,_tsDateModified,_nViewCount,_nLikeCount,_nDownloadCount,"
        "_aPreviewMedia,_aRootCategory,_aGame,_bIsObsolete"
    )

    def __init__(self, opener: Callable[..., Any] | None = None):
        self._opener = opener or urllib.request.urlopen

    def parse_mod_id(self, value: str) -> int:
        if value.isdigit():
            return int(value)
        match = re.search(r"gamebanana\.com/mods/(\d+)", value)
        if not match:
            raise StoreError("Expected a GameBanana mod URL or numeric submission ID")
        return int(match.group(1))

    def fetch(self, value: str) -> GameBananaMod:
        mod_id = self.parse_mod_id(value)
        endpoint = f"https://gamebanana.com/apiv11/Mod/{mod_id}"
        data = self._request_json(endpoint, {"_csvProperties": self.DETAIL_PROPERTIES})
        if not isinstance(data, dict):
            raise StoreError("GameBanana returned an unexpected mod response")
        return self._mod(data, fallback_id=mod_id)

    def browse(
        self,
        *,
        region: str = "global",
        page: int = 1,
        per_page: int = 24,
        sort: str = "updated",
        query: str = "",
    ) -> GameBananaPage:
        key = region.casefold()
        if key not in GAME_IDS:
            raise StoreError(f"Unsupported GameBanana game region: {region}")
        page = max(1, int(page))
        per_page = max(1, min(50, int(per_page)))
        try:
            result = self._browse_index(GAME_IDS[key], page, per_page, sort, query)
            if result.mods:
                return result
        except StoreError:
            pass
        return self._browse_new(GAME_IDS[key], page, per_page, query)

    def _browse_index(
        self,
        game_id: int,
        page: int,
        per_page: int,
        sort: str,
        query: str,
    ) -> GameBananaPage:
        order = {
            "updated": "_tsDateModified,DESC",
            "newest": "_tsDateAdded,DESC",
            "popular": "_nLikeCount,DESC",
            "downloads": "_nDownloadCount,DESC",
            "views": "_nViewCount,DESC",
        }.get(sort, "_tsDateModified,DESC")
        params = {
            "_aFilters[Generic_Game]": game_id,
            "_nPage": page,
            "_nPerpage": per_page,
            "_sOrderBy": order,
            "_csvProperties": self.DETAIL_PROPERTIES,
        }
        if query.strip():
            params["_sSearchString"] = query.strip()
        data = self._request_json("https://gamebanana.com/apiv11/Mod/Index", params)
        if not isinstance(data, dict):
            raise StoreError("GameBanana browse response was not an object")
        records = data.get("_aRecords") or []
        mods = tuple(self._mod(item) for item in records if isinstance(item, dict))
        if query.strip():
            needle = query.casefold().strip()
            mods = tuple(item for item in mods if needle in f"{item.name} {item.author} {item.description}".casefold())
        metadata = data.get("_aMetadata") or {}
        total = _int(metadata.get("_nRecordCount"))
        complete = bool(metadata.get("_bIsComplete", not mods))
        return GameBananaPage(mods, page, total, bool(mods) and not complete)

    def _browse_new(self, game_id: int, page: int, per_page: int, query: str) -> GameBananaPage:
        data = self._request_json(
            "https://api.gamebanana.com/Core/List/New",
            {
                "itemtype": "Mod",
                "gameid": game_id,
                "page": page,
                "include_updated": 1,
                "format": "json_min",
            },
        )
        ids = list(dict.fromkeys(_extract_ids(data)))[:per_page]
        mods: list[GameBananaMod] = []
        needle = query.casefold().strip()
        for mod_id in ids:
            try:
                mod = self.fetch(str(mod_id))
            except StoreError:
                continue
            if needle and needle not in f"{mod.name} {mod.author} {mod.description}".casefold():
                continue
            mods.append(mod)
        return GameBananaPage(tuple(mods), page, len(ids), len(ids) >= per_page)

    def download(
        self,
        mod: GameBananaMod,
        destination: str | Path,
        *,
        file_id: int | None = None,
        progress: Callable[[int, int], None] | None = None,
    ) -> tuple[Path, SourceSpec]:
        if not mod.files:
            raise StoreError("GameBanana submission has no downloadable files")
        selected = next((item for item in mod.files if item.id == file_id), None) if file_id else max(
            mod.files, key=lambda item: (item.date_added, item.id)
        )
        if selected is None:
            raise StoreError(f"GameBanana file not found: {file_id}")
        directory = Path(destination)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / (selected.name or f"gamebanana-{selected.id}.zip")
        request = urllib.request.Request(selected.url, headers={"User-Agent": self.USER_AGENT})
        try:
            with self._opener(request, timeout=60) as response, target.open("wb") as output:
                total = int(response.headers.get("Content-Length", "0") or 0)
                copied = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    copied += len(chunk)
                    if progress:
                        progress(copied, total)
        except Exception as exc:
            target.unlink(missing_ok=True)
            raise StoreError(f"GameBanana download failed: {exc}") from exc
        return target, SourceSpec(
            provider="gamebanana",
            url=mod.profile_url,
            submission_id=mod.id,
            file_id=selected.id,
            updated_at=selected.date_added or mod.date_updated,
        )

    def import_mod(self, store: ManagerStore, value: str, *, file_id: int | None = None):
        mod = self.fetch(value)
        archive, source = self.download(mod, store.paths.root / "downloads", file_id=file_id)
        record = store.import_archive(archive, source=source)
        record.name = mod.name
        record.author = mod.author
        record.description = mod.description
        if mod.version:
            record.version = mod.version
        store.save_mod(record)
        return record

    def update_available(self, record) -> GameBananaFile | None:
        if record.source.provider != "gamebanana" or not record.source.submission_id:
            return None
        remote = self.fetch(str(record.source.submission_id))
        if not remote.files:
            return None
        newest = max(remote.files, key=lambda item: (item.date_added, item.id))
        if newest.id != record.source.file_id or newest.date_added > (record.source.updated_at or 0):
            return newest
        return None

    def _request_json(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        url = endpoint
        if params:
            url += "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT, "Accept": "application/json"})
        try:
            with self._opener(request, timeout=30) as response:
                return json.load(response)
        except Exception as exc:
            raise StoreError(f"GameBanana request failed: {exc}") from exc

    def _mod(self, data: dict[str, Any], fallback_id: int = 0) -> GameBananaMod:
        mod_id = _int(data.get("_idRow") or data.get("_idSubmission") or fallback_id)
        files = tuple(self._file(item) for item in data.get("_aFiles", []) if isinstance(item, dict))
        submitter = data.get("_aSubmitter") or {}
        preview = data.get("_aPreviewMedia") or {}
        images = preview.get("_aImages") if isinstance(preview, dict) else []
        image_url = ""
        if isinstance(images, list) and images:
            first = images[0] if isinstance(images[0], dict) else {}
            image_url = str(first.get("_sBaseUrl") or "") + str(
                first.get("_sFile") or first.get("_sFile220") or first.get("_sFile530") or ""
            )
        category = data.get("_aRootCategory") or {}
        game = data.get("_aGame") or {}
        return GameBananaMod(
            id=mod_id,
            name=str(data.get("_sName") or f"GameBanana mod {mod_id}"),
            author=str(submitter.get("_sName") or ""),
            profile_url=str(data.get("_sProfileUrl") or f"https://gamebanana.com/mods/{mod_id}"),
            files=files,
            description=_plain_text(str(data.get("_sText") or data.get("_sDescription") or "")),
            version=str(data.get("_sVersion") or ""),
            date_added=_int(data.get("_tsDateAdded")),
            date_updated=_int(data.get("_tsDateModified") or data.get("_tsDateUpdated")),
            views=_int(data.get("_nViewCount")),
            likes=_int(data.get("_nLikeCount")),
            downloads=_int(data.get("_nDownloadCount")) or sum(item.downloads for item in files),
            image_url=image_url,
            category=str(category.get("_sName") or ""),
            game_name=str(game.get("_sName") or ""),
            obsolete=bool(data.get("_bIsObsolete")),
        )

    @staticmethod
    def _file(data: dict[str, Any]) -> GameBananaFile:
        file_id = _int(data.get("_idRow") or data.get("_idFile"))
        url = str(data.get("_sDownloadUrl") or data.get("_sDownloadUrlArchive") or "")
        if not url and file_id:
            url = f"https://gamebanana.com/dl/{file_id}"
        name = str(data.get("_sFile") or data.get("_sName") or f"file-{file_id}.zip")
        return GameBananaFile(
            id=file_id,
            name=Path(urllib.parse.urlparse(name).path).name,
            url=url,
            date_added=_int(data.get("_tsDateAdded")),
            downloads=_int(data.get("_nDownloadCount")),
        )


def _extract_ids(value: Any) -> Iterable[int]:
    if isinstance(value, int):
        if value > 0:
            yield value
    elif isinstance(value, str) and value.isdigit():
        yield int(value)
    elif isinstance(value, list):
        for item in value:
            yield from _extract_ids(item)
    elif isinstance(value, dict):
        for key in ("id", "_idRow", "_idSubmission", "_aRecords", "items", "records", "data"):
            if key in value:
                yield from _extract_ids(value[key])


def _plain_text(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(value)).strip()


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
