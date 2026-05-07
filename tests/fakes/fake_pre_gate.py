"""FakePreGateAuditor: aprova por padrão; aceita override."""
from __future__ import annotations

from contadinhos.core.schemas import PolicyCheck, Roteiro


class FakePreGateAuditor:
    def __init__(self, force: PolicyCheck | None = None) -> None:
        self.calls: list[dict] = []
        self._force = force

    def audit(self, roteiro: Roteiro) -> PolicyCheck:
        self.calls.append({"roteiro_titulo": roteiro.titulo})
        if self._force is not None:
            return self._force
        return PolicyCheck(verdict="ok", severity="low", flags=[])
