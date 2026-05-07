"""Contrato Transcriber via Fake + checks unit do OpenAITranscriber.

Real provider test (chama API paga) vive em test_real_transcribe.py com
marker `real_provider`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from contadinhos.core.transcribe import OpenAITranscriber
from tests.contracts.transcriber import TranscriberContract
from tests.fakes.fake_transcriber import FakeTranscriber


class TestFakeTranscriberContract(TranscriberContract):
    @pytest.fixture
    def transcriber(self):
        return FakeTranscriber()


def test_openai_transcriber_arquivo_inexistente_levanta_filenotfound(tmp_path):
    """Sem chamada à API: file check vem antes do decorator de retry."""
    t = OpenAITranscriber(api_key="fake-key")
    with pytest.raises(FileNotFoundError):
        t.transcribe(tmp_path / "nao_existe.m4a")


def test_openai_transcriber_construtor_aceita_model():
    t = OpenAITranscriber(api_key="fake-key", model="gpt-4o-mini-transcribe")
    assert t.model == "gpt-4o-mini-transcribe"
    # cliente é lazy — não foi inicializado
    assert t._client is None
