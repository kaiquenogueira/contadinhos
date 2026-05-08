"""Unit tests do YouTubeUploader (sem rede)."""
from __future__ import annotations

from pathlib import Path

import pytest

from contadinhos.core.upload.youtube import YouTubeUploader


def _fake_service(captured: dict, video_id: str = "abc123"):
    """Mock do youtube_v3 service expondo só videos().insert()."""

    class _Insert:
        def __init__(self, body, media_body):
            captured["body"] = body
            captured["media_body"] = media_body

        def next_chunk(self):
            return None, {
                "id": video_id,
                "snippet": {"title": captured["body"]["snippet"]["title"]},
                "status": {
                    "privacyStatus": captured["body"]["status"]["privacyStatus"]
                },
            }

    class _Videos:
        def insert(self, *, part, body, media_body):
            return _Insert(body, media_body)

    class _Service:
        def videos(self):
            return _Videos()

    return _Service()


def test_falha_em_video_inexistente(tmp_path):
    u = YouTubeUploader(credentials_provider=lambda: object())
    with pytest.raises(FileNotFoundError):
        u.upload(
            video_path=tmp_path / "missing.mp4",
            title="x", description="y", tags=[],
            made_for_kids=True, privacy_status="private",
        )


def test_made_for_kids_false_levanta(tmp_path):
    """Hard guard contra bug regressão — canal é made for kids desde dia 1."""
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    u = YouTubeUploader(credentials_provider=lambda: object())
    with pytest.raises(ValueError, match="made_for_kids"):
        u.upload(
            video_path=video,
            title="x", description="y", tags=[],
            made_for_kids=False, privacy_status="private",
        )


def test_privacy_status_invalido_levanta(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    u = YouTubeUploader(credentials_provider=lambda: object())
    with pytest.raises(ValueError, match="privacy_status"):
        u.upload(
            video_path=video,
            title="x", description="y", tags=[],
            made_for_kids=True, privacy_status="banana",
        )


def test_upload_envia_body_correto_e_retorna_url(tmp_path, placeholder_mp4):
    """Body inclui made_for_kids + categoryId + defaultLanguage; retorna url completa."""
    captured: dict = {}
    u = YouTubeUploader(credentials_provider=lambda: object())
    u._service = _fake_service(captured, video_id="test123")

    result = u.upload(
        video_path=placeholder_mp4,
        title="A raposa e a flor",
        description="Sinopse acolhedora.",
        tags=["historiainfantil", "aquarela"],
        made_for_kids=True,
        privacy_status="private",
    )
    assert result["videoId"] == "test123"
    assert result["url"] == "https://youtu.be/test123"
    assert result["status"] == "private"
    body = captured["body"]
    assert body["status"]["selfDeclaredMadeForKids"] is True
    assert body["status"]["privacyStatus"] == "private"
    assert body["snippet"]["categoryId"] == "1"
    assert body["snippet"]["defaultLanguage"] == "pt-BR"
    assert body["snippet"]["tags"] == ["historiainfantil", "aquarela"]


def test_titulo_e_descricao_sao_capados(tmp_path, placeholder_mp4):
    """YouTube limita title=100 / description=5000."""
    captured: dict = {}
    u = YouTubeUploader(credentials_provider=lambda: object())
    u._service = _fake_service(captured)

    long_title = "x" * 200
    long_desc = "y" * 6000
    u.upload(
        video_path=placeholder_mp4,
        title=long_title,
        description=long_desc,
        tags=[],
        made_for_kids=True,
        privacy_status="unlisted",
    )
    assert len(captured["body"]["snippet"]["title"]) == 100
    assert len(captured["body"]["snippet"]["description"]) == 5000


def test_credentials_provider_invocado_lazy(tmp_path, placeholder_mp4):
    """Construtor não chama credentials_provider — só na 1ª upload."""
    calls = {"n": 0}

    def provider():
        calls["n"] += 1
        return object()

    captured: dict = {}
    u = YouTubeUploader(credentials_provider=provider)
    u._service = _fake_service(captured)
    assert calls["n"] == 0  # construtor não consulta credentials
