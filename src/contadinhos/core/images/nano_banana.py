"""Imagens-chave via Nano Banana (`gemini-3.1-flash-image-preview`).

Decisions §5: 4 candidatas por imagem-chave, escolha humana via picker.
Style guide aquarela é injetado no prompt (§2). Mesma key Google que pré-gate.
"""
from __future__ import annotations

from pathlib import Path

from contadinhos.core.providers.retry import retryable
from contadinhos.core.style import apply_style


class NanoBananaImageGenerator:
    """Gera N candidatas via Gemini image model. Retorna paths em ordem."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.1-flash-image-preview",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, n: int, output_dir: Path) -> list[Path]:
        if not prompt:
            raise ValueError("prompt vazio")
        output_dir.mkdir(parents=True, exist_ok=True)
        styled_prompt = apply_style(prompt)
        outs: list[Path] = []
        for i in range(n):
            image_bytes = self._call_api(styled_prompt)
            out = output_dir / f"candidate_{i}.png"
            out.write_bytes(image_bytes)
            outs.append(out)
        return outs

    @retryable("nano_banana")
    def _call_api(self, prompt: str) -> bytes:
        client = self._ensure_client()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        for candidate in response.candidates or []:
            for part in candidate.content.parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    return inline.data
        raise RuntimeError(f"Nano Banana não retornou imagem para prompt: {prompt[:80]}")
