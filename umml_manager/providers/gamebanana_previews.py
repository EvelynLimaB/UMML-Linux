from __future__ import annotations

import urllib.parse
from dataclasses import replace
from typing import Any

from .gamebanana import GameBananaClient, GameBananaMod


class PreviewGameBananaClient(GameBananaClient):
    """GameBanana client variant that normalizes preview media for the GUI."""

    def _mod(self, data: dict[str, Any], fallback_id: int = 0) -> GameBananaMod:
        mod = super()._mod(data, fallback_id=fallback_id)
        image_url = primary_preview_url(data)
        return replace(mod, image_url=image_url or mod.image_url)


def primary_preview_url(data: dict[str, Any]) -> str:
    preview = data.get("_aPreviewMedia") or {}
    images = preview.get("_aImages") if isinstance(preview, dict) else []
    if not isinstance(images, list):
        return ""

    for item in images:
        if not isinstance(item, dict):
            continue
        base_url = str(item.get("_sBaseUrl") or "").strip()
        if not base_url:
            continue
        for field in ("_sFile530", "_sFile220", "_sFile100", "_sFile"):
            filename = str(item.get(field) or "").strip()
            if not filename:
                continue
            url = urllib.parse.urljoin(
                base_url.rstrip("/") + "/",
                filename.lstrip("/"),
            )
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme.casefold() == "https" and parsed.netloc:
                return url
    return ""
