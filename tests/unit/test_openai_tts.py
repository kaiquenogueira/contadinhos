"""Unit tests do OpenAITTS (sem rede). Espelha o padrão de test_elevenlabs_tts."""

from __future__ import annotations

import pytest

from contadinhos.core.tts.openai import OpenAITTS


def test_construtor_le_voices_yaml():
    t = OpenAITTS(api_key="fake-key")
    assert t.model == "gpt-4o-mini-tts"
    assert t.voice  # default vindo de config/voices.yaml
    assert t.style_instruction  # steering pt-BR presente


def test_synthesize_aborta_em_texto_vazio(tmp_path):
    t = OpenAITTS(api_key="fake-key")
    with pytest.raises(ValueError):
        t.synthesize(text="", voice_id="default", output_path=tmp_path / "x.wav")


class _FakeSpeechResponse:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data


class _FakeSpeech:
    def __init__(self, captured: dict, data: bytes = b"RIFFfakewav"):
        self._captured = captured
        self._data = data

    def create(self, **kwargs):
        self._captured.update(kwargs)
        return _FakeSpeechResponse(self._data)


class _FakeClient:
    def __init__(self, captured: dict):
        self.audio = type("A", (), {"speech": _FakeSpeech(captured)})()


def test_synthesize_usa_voice_default_e_passa_instructions(tmp_path):
    captured: dict = {}
    t = OpenAITTS(api_key="fake-key")
    t._client = _FakeClient(captured)
    out = t.synthesize(text="Era uma vez.", voice_id="default", output_path=tmp_path / "n.wav")
    assert out.exists()
    assert out.read_bytes() == b"RIFFfakewav"
    assert captured["model"] == "gpt-4o-mini-tts"
    assert captured["voice"] == t.voice
    assert captured["input"] == "Era uma vez."
    assert captured["response_format"] == "wav"
    assert captured["instructions"] == t.style_instruction


def test_synthesize_aceita_voice_override(tmp_path):
    captured: dict = {}
    t = OpenAITTS(api_key="fake-key")
    t._client = _FakeClient(captured)
    t.synthesize(text="x", voice_id="sage", output_path=tmp_path / "n.wav")
    assert captured["voice"] == "sage"
