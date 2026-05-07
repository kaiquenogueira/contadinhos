"""FakeTTS: gera WAV de silêncio proporcional ao tamanho do texto.

Duração ≈ len(text) * 0.05s (heurística que aproxima ritmo de narração).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"
PLACEHOLDER = FIXTURES / "audio" / "silencio_5s.wav"


class FakeTTS:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> Path:
        if not text:
            raise ValueError("texto vazio")
        self.calls.append({"text": text, "voice_id": voice_id})
        output_path.parent.mkdir(parents=True, exist_ok=True)
        duration_s = max(0.5, len(text) * 0.05)
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", str(duration_s),
                    str(output_path),
                ],
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            shutil.copyfile(PLACEHOLDER, output_path)
        return output_path
