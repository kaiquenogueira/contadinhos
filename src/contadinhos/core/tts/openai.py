"""TTS via OpenAI `gpt-4o-mini-tts` (decisions §5; Sprint 5b).

Usa a `OPENAI_API_KEY` já em mãos — zero atrito de credencial vs ElevenLabs.
`instructions` (steering de narração pt-BR) e voz default vivem em
`config/voices.yaml::openai` (config isolada, §4). Pede `response_format=wav`
→ já sai WAV com header, igual ao ElevenLabs, pronto pra montagem ffmpeg.
"""

from __future__ import annotations

from pathlib import Path

from contadinhos.core.config import load_config
from contadinhos.core.providers.retry import retryable


class OpenAITTS:
    """OpenAI TTS via SDK oficial (`audio.speech`)."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        cfg = load_config("voices")
        oai = cfg.get("openai", {})
        self.voice: str = oai.get("voice", "coral")
        self.model: str = oai.get("model", "gpt-4o-mini-tts")
        self.style_instruction: str = cfg.get("style_instruction", "")
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> Path:
        if not text:
            raise ValueError("texto vazio")
        chosen = voice_id if voice_id and voice_id != "default" else self.voice
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(self._call_api(text, chosen))
        return output_path

    @retryable("openai_tts")
    def _call_api(self, text: str, voice: str) -> bytes:
        client = self._ensure_client()
        kwargs: dict = {
            "model": self.model,
            "voice": voice,
            "input": text,
            "response_format": "wav",
        }
        if self.style_instruction:
            kwargs["instructions"] = self.style_instruction
        return client.audio.speech.create(**kwargs).read()
