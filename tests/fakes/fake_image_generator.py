"""FakeImageGenerator: copia placeholder PNG N vezes."""
from __future__ import annotations

import shutil
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"
PLACEHOLDER = FIXTURES / "images" / "placeholder.png"


class FakeImageGenerator:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, prompt: str, n: int, output_dir: Path) -> list[Path]:
        if not prompt:
            raise ValueError("prompt vazio")
        self.calls.append({"prompt": prompt, "n": n})
        output_dir.mkdir(parents=True, exist_ok=True)
        outs = []
        for i in range(n):
            p = output_dir / f"candidate_{i}.png"
            shutil.copyfile(PLACEHOLDER, p)
            outs.append(p)
        return outs
