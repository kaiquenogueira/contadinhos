"""Vídeo via Veo 3.1 (`veo-3.1-generate-preview`).

Decisions §5: provider-agnostic via `VideoGenerator`. Veo é default por
crédito Google. I2V usa `first_frame`; T2V só prompt. Long-running operation:
submete → polla até `.done` → escreve bytes em `output_path`.
"""
from __future__ import annotations

import time
from pathlib import Path

from contadinhos.core.providers.retry import retryable
from contadinhos.core.style import apply_style


class Veo31VideoGenerator:
    """Vídeo via Veo 3.1 (long-running operation)."""

    def __init__(
        self,
        api_key: str,
        model: str = "veo-3.1-generate-preview",
        poll_interval_s: float = 10.0,
        max_wait_s: float = 600.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.poll_interval_s = poll_interval_s
        self.max_wait_s = max_wait_s
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(
        self,
        prompt: str,
        duration_s: float,
        output_path: Path,
        first_frame: Path | None = None,
    ) -> Path:
        if not prompt:
            raise ValueError("prompt vazio")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        styled = apply_style(prompt)
        video_bytes = self._call_api(styled, duration_s, first_frame)
        output_path.write_bytes(video_bytes)
        return output_path

    @retryable("veo")
    def _call_api(
        self, prompt: str, duration_s: float, first_frame: Path | None
    ) -> bytes:
        from google.genai import types

        client = self._ensure_client()
        image = None
        if first_frame is not None:
            image = types.Image(
                image_bytes=first_frame.read_bytes(),
                mime_type="image/png",
            )
        source = types.GenerateVideosSource(prompt=prompt, image=image)
        config = types.GenerateVideosConfig(durationSeconds=int(round(duration_s)))
        operation = client.models.generate_videos(
            model=self.model, source=source, config=config
        )
        operation = self._wait_for(operation)
        if operation.error:
            raise RuntimeError(f"Veo retornou erro: {operation.error}")
        if not operation.result or not operation.result.generated_videos:
            raise RuntimeError("Veo concluiu sem vídeo gerado")
        video = operation.result.generated_videos[0].video
        if getattr(video, "video_bytes", None):
            return video.video_bytes
        if getattr(video, "uri", None):
            # fallback: download pela files API
            return client.files.download(file=video).video_bytes
        raise RuntimeError("Veo não expôs bytes nem URI do vídeo")

    def _wait_for(self, operation):
        client = self._ensure_client()
        elapsed = 0.0
        while not operation.done:
            if elapsed >= self.max_wait_s:
                raise RuntimeError(f"Veo timeout após {self.max_wait_s}s")
            if self.poll_interval_s > 0:
                time.sleep(self.poll_interval_s)
                elapsed += self.poll_interval_s
            else:
                elapsed += 0.001  # avança contador em modo teste sem sleep
            operation = client.operations.get(operation)
        return operation
