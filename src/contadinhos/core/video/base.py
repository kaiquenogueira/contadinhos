"""Interface de geração de vídeo (§4, §5)."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class VideoGenerator(Protocol):
    def generate(
        self,
        prompt: str,
        duration_s: float,
        output_path: Path,
        first_frame: Path | None = None,
    ) -> Path: ...
