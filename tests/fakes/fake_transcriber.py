"""FakeTranscriber: retorna transcript fixo."""
from __future__ import annotations

from pathlib import Path

DEFAULT_TRANSCRIPT = (
    "Era uma vez uma raposa muito curiosa que vivia perto de um jardim. "
    "Um dia, ela viu uma flor diferente que parecia cantar quando o vento passava. "
    "A raposa se aproximou e fez amizade com a flor."
)


class FakeTranscriber:
    def __init__(self, transcript: str = DEFAULT_TRANSCRIPT) -> None:
        self.calls: list[dict] = []
        self._transcript = transcript

    def transcribe(self, audio_path: Path) -> str:
        if not audio_path.exists():
            raise FileNotFoundError(f"áudio não encontrado: {audio_path}")
        self.calls.append({"audio_path": audio_path})
        return self._transcript
