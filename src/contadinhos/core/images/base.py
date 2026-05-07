"""Interface de geração de imagens."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ImageGenerator(Protocol):
    def generate(
        self,
        prompt: str,
        n: int,
        output_dir: Path,
    ) -> list[Path]: ...
