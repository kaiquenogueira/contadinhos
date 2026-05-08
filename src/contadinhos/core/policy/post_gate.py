"""Pós-gate multimodal sobre `final.mp4` (decisions §7.2).

`gemini-2.5-flash` lê o MP4 inteiro via Files API. Pega modos de falha
visuais (glitch, vibe sombria emergente) que o pré-gate não vê.
"""
from __future__ import annotations

import time
from pathlib import Path

from contadinhos.core.config import DEFAULT_CONFIG_DIR
from contadinhos.core.policy.pre_gate import parse_audit_response
from contadinhos.core.providers.retry import retryable
from contadinhos.core.schemas import PolicyCheck


_PROMPT_PATH = DEFAULT_CONFIG_DIR / "prompts" / "post_gate.md"


class GeminiPostGate:
    """Pós-gate multimodal via gemini-2.5-flash + Files API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        prompt_path: Path | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.prompt_path = prompt_path or _PROMPT_PATH
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def audit(self, video_path: Path) -> PolicyCheck:
        if not video_path.exists():
            raise FileNotFoundError(f"vídeo ausente: {video_path}")
        return self._call_api(video_path)

    @retryable("post_gate")
    def _call_api(self, video_path: Path) -> PolicyCheck:
        client = self._ensure_client()
        prompt = self.prompt_path.read_text()

        # Files API: upload do MP4. Gemini precisa esperar processing → ACTIVE.
        file_obj = client.files.upload(file=str(video_path))
        file_obj = self._wait_for_active(file_obj)

        response = client.models.generate_content(
            model=self.model,
            contents=[file_obj, prompt],
        )
        try:
            return parse_audit_response(response.text)
        finally:
            try:
                client.files.delete(name=file_obj.name)
            except Exception:
                pass  # cleanup best-effort

    def _wait_for_active(self, file_obj):
        """Polla até `state == ACTIVE` (Gemini processa vídeo upload)."""
        client = self._ensure_client()
        for _ in range(60):  # ~60s timeout
            state = getattr(file_obj.state, "name", str(file_obj.state))
            if state == "ACTIVE":
                return file_obj
            if state == "FAILED":
                raise RuntimeError(f"upload Gemini falhou: {file_obj.name}")
            time.sleep(1)
            file_obj = client.files.get(name=file_obj.name)
        raise RuntimeError(f"timeout aguardando ACTIVE em {file_obj.name}")
