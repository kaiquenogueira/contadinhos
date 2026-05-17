"""Unit tests do GeminiTTS (sem rede).

Gemini TTS devolve PCM cru (24 kHz, 16-bit, mono); o provider precisa
envelopar em WAV com header pra montagem ffmpeg downstream tratar igual ao
ElevenLabs (que já vem WAV). Esse envelope é a lógica real testada aqui.
"""

from __future__ import annotations

import wave

import pytest

from contadinhos.core.tts.gemini import GeminiTTS


def test_construtor_le_voices_yaml():
    t = GeminiTTS(api_key="fake-key")
    assert t.model
    assert t.voice
    assert t.style_instruction


def test_synthesize_aborta_em_texto_vazio(tmp_path):
    t = GeminiTTS(api_key="fake-key")
    with pytest.raises(ValueError):
        t.synthesize(text="", voice_id="default", output_path=tmp_path / "x.wav")


def test_pcm_to_wav_gera_wav_valido():
    pcm = b"\x01\x00" * 1200
    wav = GeminiTTS._pcm_to_wav(pcm, sample_rate=24000)
    assert wav[:4] == b"RIFF"
    assert wav[8:12] == b"WAVE"


def test_synthesize_envelopa_pcm_em_wav(tmp_path, monkeypatch):
    t = GeminiTTS(api_key="fake-key")
    pcm = b"\x02\x00" * 600
    monkeypatch.setattr(t, "_call_api", lambda text, voice: pcm)
    out = t.synthesize(text="Olá.", voice_id="default", output_path=tmp_path / "n.wav")
    assert out.exists()
    assert out.read_bytes()[:4] == b"RIFF"
    with wave.open(str(out), "rb") as w:
        assert w.getframerate() == 24000
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getnframes() == 600
