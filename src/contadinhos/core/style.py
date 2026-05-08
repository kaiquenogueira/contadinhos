"""Style guide canônico (decisions §2): "aquarela / livro infantil ilustrado".

Função pura — providers reais de imagem e vídeo aplicam ao `prompt_visual`
antes de mandar pro modelo.
"""
from __future__ import annotations

from contadinhos.core.config import load_config


def style_string() -> str:
    """Lê estilo aquarela do `config/style.yaml`."""
    cfg = load_config("style")
    return cfg.get("aquarela", "")


def apply_style(prompt: str) -> str:
    """Prepende o style guide ao prompt. Idempotente.

    Se o prompt já contém o style guide (substring case-insensitive), retorna
    inalterado pra evitar duplicação em retries ou pipelines encadeados.
    """
    style = style_string()
    if not style:
        return prompt
    if style.lower() in prompt.lower():
        return prompt
    return f"{style}. {prompt}"
