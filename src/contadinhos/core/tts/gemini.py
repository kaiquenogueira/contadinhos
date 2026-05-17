"""TTS via Gemini 2.5 Flash TTS (decisions §5; Sprint 5b).

Usa a mesma `GOOGLE_GENERATIVE_AI_API_KEY` do Veo/Nano Banana/gates —
consolida tudo numa key/crédito Google (memória `project_google_auth`).

Gemini TTS devolve **PCM cru** (16-bit, mono, 24 kHz), não WAV. O provider
envelopa em WAV com header pra montagem ffmpeg tratar igual ao ElevenLabs.
Steering de estilo: Gemini não tem campo `instructions` separado — a
diretiva pt-BR (`config/voices.yaml::style_instruction`) é prefixada ao
texto, como a doc de speech-generation recomenda.
"""

from __future__ import annotations

import io
import wave
from pathlib import Path

from contadinhos.core.config import load_config
from contadinhos.core.providers.retry import retryable

_SAMPLE_RATE = 24000  # Gemini TTS: PCM 16-bit mono @ 24 kHz


class GeminiTTS:
    """Gemini 2.5 Flash TTS via `google-genai`."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        cfg = load_config("voices")
        gem = cfg.get("gemini", {})
        self.voice: str = gem.get("voice", "Sulafat")
        self.model: str = gem.get("model", "gemini-2.5-flash-preview-tts")
        self.style_instruction: str = cfg.get("style_instruction", "")
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> Path:
        if not text:
            raise ValueError("texto vazio")
        chosen = voice_id if voice_id and voice_id != "default" else self.voice
        pcm = self._call_api(text, chosen)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(self._pcm_to_wav(pcm, _SAMPLE_RATE))
        return output_path

    @retryable("gemini_tts")
    def _call_api(self, text: str, voice: str) -> bytes:
        from google.genai import types

        client = self._ensure_client()
        prompt = f"{self.style_instruction}\n\n{text}" if self.style_instruction else text
        resp = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                    )
                ),
            ),
        )
        return resp.candidates[0].content.parts[0].inline_data.data

    @staticmethod
    def _pcm_to_wav(pcm: bytes, sample_rate: int = _SAMPLE_RATE) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)  # 16-bit
            w.setframerate(sample_rate)
            w.writeframes(pcm)
        return buf.getvalue()
