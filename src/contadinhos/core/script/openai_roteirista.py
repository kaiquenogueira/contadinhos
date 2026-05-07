"""Roteirista via OpenAI gpt-5-mini com structured outputs (decisions §3, §3.3).

Mini-first: gpt-5-mini é default. Subir pra gpt-5 só com evidência empírica
de calibração (memória `feedback_mini_first`).
"""
from __future__ import annotations

from pathlib import Path

from contadinhos.core.config import DEFAULT_CONFIG_DIR
from contadinhos.core.providers.retry import retryable
from contadinhos.core.schemas import Roteiro


_PROMPT_PATH = DEFAULT_CONFIG_DIR / "prompts" / "roteirista.md"


def render_prompt(
    transcript: str,
    target_duration_s: float,
    prompt_path: Path | None = None,
) -> str:
    template = (prompt_path or _PROMPT_PATH).read_text()
    return (
        template
        .replace("{{TARGET_DURATION_S}}", str(int(target_duration_s)))
        .replace("{{TRANSCRIPT}}", transcript)
    )


class OpenAIRoteirista:
    """Roteirista via gpt-5-mini com structured outputs em `Roteiro`."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",
        prompt_path: Path | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.prompt_path = prompt_path or _PROMPT_PATH
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    @retryable("script")
    def generate(self, transcript: str, target_duration_s: float) -> Roteiro:
        client = self._ensure_client()
        prompt = render_prompt(transcript, target_duration_s, self.prompt_path)
        completion = client.beta.chat.completions.parse(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format=Roteiro,
        )
        roteiro = completion.choices[0].message.parsed
        if roteiro is None:
            raise RuntimeError("roteirista retornou None — refusal ou parse falhou")
        return roteiro
