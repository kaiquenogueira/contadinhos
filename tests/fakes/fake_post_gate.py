"""FakePostGate: aprova por padrão; aceita override."""
from __future__ import annotations

from pathlib import Path

from contadinhos.core.schemas import PolicyCheck


class FakePostGate:
    def __init__(self, force: PolicyCheck | None = None) -> None:
        self.calls: list[dict] = []
        self._force = force

    def audit(self, video_path: Path) -> PolicyCheck:
        self.calls.append({"video_path": video_path})
        if self._force is not None:
            return self._force
        return PolicyCheck(verdict="ok", severity="low", flags=[])
