"""FakeRoteirista: lê fixture valido_completo.json."""
from __future__ import annotations

import json
from pathlib import Path

from contadinhos.core.schemas import Roteiro

FIXTURES = Path(__file__).parent.parent / "fixtures"


class FakeRoteirista:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, transcript: str, target_duration_s: float) -> Roteiro:
        self.calls.append({"transcript": transcript, "target_duration_s": target_duration_s})
        raw = json.loads((FIXTURES / "roteiros" / "valido_completo.json").read_text())
        return Roteiro.model_validate(raw)
