"""Interface de upload (YouTube)."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class YouTubeUploader(Protocol):
    def upload(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str],
        made_for_kids: bool,
        privacy_status: str,
        thumbnail_path: Path | None = None,
    ) -> dict: ...
