"""Contract test for YouTubeUploader."""
import pytest


class YouTubeUploaderContract:
    @pytest.fixture
    def uploader(self):
        raise NotImplementedError

    def test_upload_retorna_video_id(self, uploader, placeholder_mp4):
        result = uploader.upload(
            video_path=placeholder_mp4,
            title="Teste | contadinhos",
            description="desc",
            tags=["a", "b"],
            made_for_kids=True,
            privacy_status="private",
        )
        assert "videoId" in result
        assert result["videoId"]
