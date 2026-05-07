"""Interfaces dos gates de policy (§7)."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from contadinhos.core.schemas import PolicyCheck, Roteiro


class PreGateAuditor(Protocol):
    def audit(self, roteiro: Roteiro) -> PolicyCheck: ...


class PostGate(Protocol):
    def audit(self, video_path: Path) -> PolicyCheck: ...
