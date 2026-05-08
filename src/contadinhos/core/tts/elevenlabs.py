"""TTS via ElevenLabs (decisions §5).

Lê config de `config/voices.yaml`. `voice_id` pode vir do caller (override
por cena ou personagem) ou do config (default canal). Output WAV 24 kHz.
"""
from __future__ import annotations

from pathlib import Path

from contadinhos.core.config import load_config
from contadinhos.core.providers.retry import retryable


class ElevenLabsTTS:
    """ElevenLabs TTS via SDK oficial."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        cfg = load_config("voices")
        self.default_voice_id: str = cfg.get("default_voice_id") or ""
        self.model_id: str = cfg.get("model_id", "eleven_multilingual_v2")
        self.output_format: str = cfg.get("output_format", "wav_24000")
        self.voice_settings: dict = cfg.get("voice_settings", {})
        self.model = self.model_id  # exposto pra cost ledger
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from elevenlabs.client import ElevenLabs
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> Path:
        if not text:
            raise ValueError("texto vazio")
        chosen_voice = voice_id if voice_id and voice_id != "default" else self.default_voice_id
        if not chosen_voice:
            raise RuntimeError(
                "voice_id não fornecido e default_voice_id ausente em config/voices.yaml"
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        audio_bytes = self._call_api(text, chosen_voice)
        output_path.write_bytes(audio_bytes)
        return output_path

    @retryable("elevenlabs")
    def _call_api(self, text: str, voice_id: str) -> bytes:
        from elevenlabs import VoiceSettings

        client = self._ensure_client()
        kwargs: dict = {
            "voice_id": voice_id,
            "text": text,
            "model_id": self.model_id,
            "output_format": self.output_format,
        }
        if self.voice_settings:
            kwargs["voice_settings"] = VoiceSettings(**self.voice_settings)
        chunks = client.text_to_speech.convert(**kwargs)
        return b"".join(chunks)
