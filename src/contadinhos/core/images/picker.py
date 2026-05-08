"""Escolha de candidata de imagem-chave (decisions §13 fase 3).

`run_images` gera N candidatas; humano escolhe via `pick_candidate` que cria
`chosen.png` como **cópia** (não symlink — Sprint 3 §13).
"""
from __future__ import annotations

from contadinhos.core.story import Story


def pick_candidate(story: Story, img_id: str, candidate_idx: int) -> None:
    """Copia `candidate_<idx>.png` como `chosen.png` em `images/<img_id>/`.

    Levanta `FileNotFoundError` se o índice não existir. Sobrescreve `chosen.png`
    se já houver (re-pick é livre).
    """
    img_dir = story.path / "images" / img_id
    candidate = img_dir / f"candidate_{candidate_idx}.png"
    if not candidate.exists():
        raise FileNotFoundError(f"candidata não existe: {candidate}")
    chosen = img_dir / "chosen.png"
    chosen.write_bytes(candidate.read_bytes())
