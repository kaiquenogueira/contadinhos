"""Interface do roteirista (LLM)."""
from __future__ import annotations

from typing import Protocol

from contadinhos.core.schemas import Roteiro


class Roteirista(Protocol):
    def generate(self, transcript: str, target_duration_s: float) -> Roteiro: ...
