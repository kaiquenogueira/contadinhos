"""YouTube uploader real (decisions §1, made_for_kids obrigatório).

Resumable upload via google-api-python-client. Lazy-load do client de
credenciais — instância fica leve e testável sem rede. `made_for_kids=True`
é hard-coded em `__init__` pra prevenir regressão (decisions §1).
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from contadinhos.core.providers.retry import retryable
from contadinhos.core.upload.auth import require_credentials


class YouTubeUploader:
    """Sobe vídeo via `videos().insert()` com `made_for_kids=True`."""

    def __init__(
        self,
        credentials_provider: Callable | None = None,
        category_id: str = "1",
        default_language: str = "pt-BR",
    ) -> None:
        self._credentials_provider = credentials_provider or require_credentials
        self.category_id = category_id
        self.default_language = default_language
        self.model = "youtube-data-api-v3"  # exposto pra cost ledger
        self._service = None

    def _ensure_service(self):
        if self._service is None:
            from googleapiclient.discovery import build
            creds = self._credentials_provider()
            self._service = build("youtube", "v3", credentials=creds, cache_discovery=False)
        return self._service

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
        if not video_path.exists():
            raise FileNotFoundError(f"vídeo ausente: {video_path}")
        if not made_for_kids:
            raise ValueError(
                "made_for_kids=True é obrigatório no canal contadinhos (decisions §1)"
            )
        if privacy_status not in {"private", "unlisted", "public"}:
            raise ValueError(f"privacy_status inválido: {privacy_status}")
        return self._call_api(
            video_path, title, description, tags, privacy_status, thumbnail_path
        )

    @retryable("youtube_upload")
    def _call_api(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str],
        privacy_status: str,
        thumbnail_path: Path | None,
    ) -> dict:
        service = self._ensure_service()
        body = {
            "snippet": {
                "title": title[:100],  # YouTube cap
                "description": description[:5000],
                "tags": tags,
                "categoryId": self.category_id,
                "defaultLanguage": self.default_language,
                "defaultAudioLanguage": self.default_language,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": True,
                "license": "youtube",
                "embeddable": True,
            },
        }
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=8 * 1024 * 1024,
        )
        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )
        response = None
        while response is None:
            _, response = request.next_chunk()

        video_id = response["id"]
        result = {
            "videoId": video_id,
            "url": f"https://youtu.be/{video_id}",
            "status": response.get("status", {}).get("privacyStatus", privacy_status),
            "title": response.get("snippet", {}).get("title", title),
        }

        if thumbnail_path is not None and thumbnail_path.exists():
            from googleapiclient.http import MediaFileUpload as _Upload

            service.thumbnails().set(
                videoId=video_id,
                media_body=_Upload(str(thumbnail_path), mimetype="image/png"),
            ).execute()
            result["thumbnail_uploaded"] = True

        return result
