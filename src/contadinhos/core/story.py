"""Story = unidade de trabalho do pipeline.

Estrutura padrão em §9.6 de `docs/decisions.md`. Filesystem-as-state.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from contadinhos.core.schemas import Roteiro


@dataclass
class Story:
    path: Path

    @classmethod
    def create(
        cls,
        slug: str,
        base_dir: Path,
        today: dt.date | None = None,
    ) -> Story:
        """Cria `<base_dir>/<YYYY-MM-DD>-<slug>/` com estrutura padrão.

        Em colisão, adiciona sufixo `-2`, `-3`, ... (§9.8).
        """
        date_str = (today or dt.date.today()).isoformat()
        attempt = 1
        while True:
            name = f"{date_str}-{slug}" if attempt == 1 else f"{date_str}-{slug}-{attempt}"
            path = base_dir / name
            if not path.exists():
                break
            attempt += 1

        path.mkdir(parents=True)
        for sub in ("images", "clips", "audio"):
            (path / sub).mkdir()
        return cls(path=path)

    @classmethod
    def load(cls, path: Path) -> Story:
        if not path.exists():
            raise FileNotFoundError(f"story não encontrada em {path}")
        return cls(path=path)

    def read_roteiro(self) -> Roteiro:
        return Roteiro.model_validate_json((self.path / "roteiro.json").read_text())

    def write_roteiro(self, roteiro: Roteiro) -> None:
        (self.path / "roteiro.json").write_text(
            roteiro.model_dump_json(indent=2)
        )

    def next_action(self) -> str:
        """Retorna a próxima etapa baseada nos arquivos presentes na story.

        Estados ordenados:
            new → transcribe → script → images → video → tts → assemble →
            policy_post → publish → done
        """
        if not (self.path / "audio.m4a").exists():
            return "new"
        if not (self.path / "transcript.txt").exists():
            return "transcribe"
        if not (self.path / "roteiro.json").exists():
            return "script"
        roteiro = self.read_roteiro()
        # imagens-chave aprovadas: cada personagem tem chosen.png
        for img in roteiro.imagens_chave:
            if not (self.path / "images" / img.id / "chosen.png").exists():
                return "images"
        # clipes: um por cena
        for cena in roteiro.cenas:
            if not (self.path / "clips" / f"scene_{cena.idx:02d}.mp4").exists():
                return "video"
        # narrações: uma por cena
        for cena in roteiro.cenas:
            if not (self.path / "audio" / f"narration_{cena.idx:02d}.wav").exists():
                return "tts"
        if not (self.path / "final.mp4").exists():
            return "assemble"
        if not (self.path / "policy_check_post.json").exists():
            return "policy_post"
        if not (self.path / "upload_result.json").exists():
            return "publish"
        return "done"

    @contextlib.contextmanager
    def lock(self) -> Iterator[None]:
        """Lock advisory por story via fcntl.flock (§9.7).

        Bloqueia outro processo de mexer na mesma story. Não-blocking:
        levanta `BlockingIOError` se lock já tomado.
        """
        lock_path = self.path / ".lock"
        f = lock_path.open("w")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
            except Exception:
                pass
            f.close()
