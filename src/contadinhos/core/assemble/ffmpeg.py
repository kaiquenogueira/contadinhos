"""Montagem do final.mp4 via ffmpeg.

Sprint 1: concat dos clips das cenas (sem mix de áudio sofisticado, sem
drawtext). Sprint 4 expande pra mix de narração + música + legenda.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from contadinhos.core.schemas import Roteiro


def concat_clips(roteiro: Roteiro, story_path: Path) -> Path:
    """Concatena os clips das cenas em ordem de `idx` em `final.mp4`.

    Implementação Sprint 1 (intencionalmente simples, sem áudio): usa
    concat demuxer do ffmpeg com lista temporária.
    """
    clips_dir = story_path / "clips"
    output = story_path / "final.mp4"

    cenas_ordenadas = sorted(roteiro.cenas, key=lambda c: c.idx)
    clip_paths = [clips_dir / f"scene_{c.idx:02d}.mp4" for c in cenas_ordenadas]
    for p in clip_paths:
        if not p.exists():
            raise FileNotFoundError(f"clip ausente: {p}")

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in clip_paths:
            f.write(f"file '{p.resolve()}'\n")
        list_path = Path(f.name)

    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "concat", "-safe", "0",
                "-i", str(list_path),
                "-c", "copy",
                str(output),
            ],
            check=True,
        )
    finally:
        list_path.unlink(missing_ok=True)

    return output
