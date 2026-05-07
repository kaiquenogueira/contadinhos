"""FakeVideoGenerator: copia placeholder MP4. Registra calls (§20.6 e)."""
from __future__ import annotations

import shutil
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"
PLACEHOLDER = FIXTURES / "video" / "placeholder_5s.mp4"


class FakeVideoGenerator:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(
        self,
        prompt: str,
        duration_s: float,
        output_path: Path,
        first_frame: Path | None = None,
    ) -> Path:
        if not prompt:
            raise ValueError("prompt vazio")
        self.calls.append(
            {"prompt": prompt, "duration_s": duration_s, "first_frame": first_frame}
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PLACEHOLDER, output_path)
        return output_path
