"""FakeYouTubeUploader: grava resultado fake sem chamar YouTube."""
from __future__ import annotations

from pathlib import Path


class FakeYouTubeUploader:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def upload(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str],
        made_for_kids: bool,
        privacy_status: str,
        thumbnail_path: Path | None = None,
    ) -> dict:
        self.calls.append(
            {
                "video_path": video_path,
                "title": title,
                "tags": tags,
                "made_for_kids": made_for_kids,
                "privacy_status": privacy_status,
            }
        )
        video_id = f"fake-{abs(hash(str(video_path))) % 10**8}"
        return {
            "videoId": video_id,
            "url": f"https://youtu.be/{video_id}",
            "status": privacy_status,
            "title": title,
        }
