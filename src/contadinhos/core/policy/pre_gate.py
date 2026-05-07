"""Pré-gate via gemini-2.5-flash (decisions §7.1).

Auditor de conteúdo infantil — chamada LLM **separada** do roteirista pra
evitar conflito de interesse (autor não é juiz de si mesmo).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from contadinhos.core.config import DEFAULT_CONFIG_DIR
from contadinhos.core.providers.retry import retryable
from contadinhos.core.schemas import PolicyCheck, Roteiro


_PROMPT_PATH = DEFAULT_CONFIG_DIR / "prompts" / "pre_gate.md"
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _strip_fences(raw: str) -> str:
    """Remove cercas markdown se modelo retornou ```json ... ```."""
    match = _FENCE_RE.search(raw.strip())
    return match.group(1).strip() if match else raw.strip()


def parse_audit_response(raw: str) -> PolicyCheck:
    """Valida JSON do auditor contra `PolicyCheck`.

    Schema fechado: categorias fora do enum levantam `pydantic.ValidationError`
    (não silencia — política de §20.2).
    """
    payload = json.loads(_strip_fences(raw))
    return PolicyCheck.model_validate(payload)


def render_prompt(roteiro: Roteiro, prompt_path: Path | None = None) -> str:
    template = (prompt_path or _PROMPT_PATH).read_text()
    return template.replace("{{ROTEIRO_JSON}}", roteiro.model_dump_json(indent=2))


class GeminiPreGateAuditor:
    """Pré-gate via google-genai. Provider distinto do roteirista (§7.1)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        prompt_path: Path | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.prompt_path = prompt_path or _PROMPT_PATH
        self._client = None  # lazy: não conecta no construtor (test friendly)

    def _ensure_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @retryable("pre_gate")
    def audit(self, roteiro: Roteiro) -> PolicyCheck:
        client = self._ensure_client()
        prompt = render_prompt(roteiro, self.prompt_path)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return parse_audit_response(response.text)
