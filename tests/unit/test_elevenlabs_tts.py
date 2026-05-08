"""Unit tests do ElevenLabsTTS (sem rede)."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from contadinhos.core.tts.elevenlabs import ElevenLabsTTS


def test_construtor_lê_voices_yaml():
    t = ElevenLabsTTS(api_key="fake-key")
    # default voice id está em config/voices.yaml (Sprint 4 #25)
    assert t.default_voice_id
    assert t.model_id == "eleven_multilingual_v2"
    assert t.output_format == "wav_24000"


def test_synthesize_aborta_em_texto_vazio(tmp_path):
    t = ElevenLabsTTS(api_key="fake-key")
    with pytest.raises(ValueError):
        t.synthesize(text="", voice_id="default", output_path=tmp_path / "x.wav")


def test_synthesize_usa_default_voice_quando_voice_id_default(tmp_path):
    captured: dict = {}

    class _FakeTTSClient:
        def convert(self, **kwargs):
            captured.update(kwargs)
            return iter([b"RIFF", b"\x00\x00\x00\x00", b"WAVEfake"])

    class _FakeClient:
        def __init__(self):
            self.text_to_speech = _FakeTTSClient()

    t = ElevenLabsTTS(api_key="fake-key")
    t._client = _FakeClient()
    out = t.synthesize(
        text="Era uma vez uma raposa.",
        voice_id="default",
        output_path=tmp_path / "n.wav",
    )
    assert out.exists()
    assert out.read_bytes().startswith(b"RIFF")
    assert captured["voice_id"] == t.default_voice_id
    assert captured["model_id"] == "eleven_multilingual_v2"
    assert captured["output_format"] == "wav_24000"


def test_synthesize_aceita_voice_id_override(tmp_path):
    captured: dict = {}

    class _FakeTTSClient:
        def convert(self, **kwargs):
            captured.update(kwargs)
            return iter([b"RIFFfake"])

    class _FakeClient:
        def __init__(self):
            self.text_to_speech = _FakeTTSClient()

    t = ElevenLabsTTS(api_key="fake-key")
    t._client = _FakeClient()
    t.synthesize(
        text="x",
        voice_id="custom_voice_xyz",
        output_path=tmp_path / "n.wav",
    )
    assert captured["voice_id"] == "custom_voice_xyz"


def test_synthesize_falha_se_voice_id_e_default_ambos_vazios(tmp_path, monkeypatch):
    t = ElevenLabsTTS(api_key="fake-key")
    t.default_voice_id = ""
    with pytest.raises(RuntimeError, match="voice_id"):
        t.synthesize(text="x", voice_id="default", output_path=tmp_path / "n.wav")


def test_synthesize_concatena_chunks_iterator(tmp_path):
    """SDK retorna Iterator[bytes] — provider concatena."""

    class _FakeTTSClient:
        def convert(self, **kwargs):
            return iter([b"AAA", b"BBB", b"CCC"])

    class _FakeClient:
        def __init__(self):
            self.text_to_speech = _FakeTTSClient()

    t = ElevenLabsTTS(api_key="fake-key")
    t._client = _FakeClient()
    out = t.synthesize(text="x", voice_id="v", output_path=tmp_path / "n.wav")
    assert out.read_bytes() == b"AAABBBCCC"
