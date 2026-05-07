"""Interface de TTS."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class TTSProvider(Protocol):
    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
    ) -> Path: ...
