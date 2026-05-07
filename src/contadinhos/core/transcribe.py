"""Transcrição via OpenAI gpt-4o-transcribe (decisions §3, §11.3).

Provider real + Protocol. Fake vive em tests/fakes/fake_transcriber.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from contadinhos.core.providers.retry import retryable


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> str: ...


class OpenAITranscriber:
    """Transcrição via gpt-4o-transcribe (sucessor do whisper-1)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-transcribe",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def transcribe(self, audio_path: Path) -> str:
        if not audio_path.exists():
            raise FileNotFoundError(f"áudio não encontrado: {audio_path}")
        return self._call_api(audio_path)

    @retryable("transcribe")
    def _call_api(self, audio_path: Path) -> str:
        client = self._ensure_client()
        with audio_path.open("rb") as f:
            result = client.audio.transcriptions.create(
                model=self.model,
                file=f,
                response_format="text",
            )
        return result if isinstance(result, str) else result.text
