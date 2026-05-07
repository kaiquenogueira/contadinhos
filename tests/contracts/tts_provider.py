"""Contract test for TTSProvider."""
from pathlib import Path

import pytest


class TTSProviderContract:
    @pytest.fixture
    def provider(self):
        raise NotImplementedError

    def test_synthesize_retorna_audio(self, provider, tmp_path):
        out = provider.synthesize(
            text="Era uma vez uma raposa.",
            voice_id="default",
            output_path=tmp_path / "narration.wav",
        )
        assert Path(out).exists()
        assert Path(out).stat().st_size > 0

    def test_aborta_em_texto_vazio(self, provider, tmp_path):
        with pytest.raises(ValueError):
            provider.synthesize(text="", voice_id="default", output_path=tmp_path / "x.wav")
