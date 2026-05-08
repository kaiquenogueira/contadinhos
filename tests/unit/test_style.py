"""Style injection pura (decisions §2 — aquarela / livro infantil)."""
from __future__ import annotations

from contadinhos.core.style import apply_style, style_string


def test_style_string_lida_de_config():
    s = style_string()
    assert "aquarela" in s.lower()


def test_apply_style_prepende_estilo():
    out = apply_style("uma raposa caminhando no jardim")
    assert "uma raposa caminhando no jardim" in out
    assert "aquarela" in out.lower()


def test_apply_style_idempotente():
    """Se prompt já contém o style guide, não duplica."""
    once = apply_style("uma raposa")
    twice = apply_style(once)
    assert twice.lower().count("aquarela") == once.lower().count("aquarela")
