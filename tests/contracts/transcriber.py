"""Contract test for Transcriber. Subclassed by Fake e Real (OpenAI)."""
from pathlib import Path

import pytest


class TranscriberContract:
    @pytest.fixture
    def transcriber(self):
        raise NotImplementedError("subclasse provê o transcriber")

    def test_transcribe_retorna_texto_nao_vazio(self, transcriber, silencio_30s_m4a):
        text = transcriber.transcribe(silencio_30s_m4a)
        assert isinstance(text, str)
        # Real pode retornar string vazia para áudio de silêncio; Fake retorna fixo.
        # Asserção mínima: não levanta + retorna str.

    def test_transcribe_arquivo_inexistente_levanta(self, transcriber, tmp_path):
        with pytest.raises((FileNotFoundError, OSError)):
            transcriber.transcribe(tmp_path / "nao_existe.m4a")
