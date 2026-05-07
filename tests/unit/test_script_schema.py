"""Schema strictness do roteirista (decisions §3.1, §8.3).

Output do gpt-5-mini deve passar pydantic; outputs malformados levantam
ValidationError pra ser tratado upstream (não silenciar, §20.2).
"""
import pytest
from pydantic import ValidationError

from contadinhos.core.schemas import Roteiro


def test_roteiro_sem_sinopse_curta_falha():
    with pytest.raises(ValidationError):
        Roteiro.model_validate({
            "titulo": "x",
            "duracao_total_s": 10,
            "personagens": [],
            "imagens_chave": [],
            "cenas": [{"idx": 1, "modo": "t2v", "prompt_visual": "x", "narracao": "y", "duracao_s": 5}],
        })


def test_roteiro_cena_modo_invalido_falha():
    with pytest.raises(ValidationError):
        Roteiro.model_validate({
            "titulo": "x",
            "sinopse_curta": "y",
            "duracao_total_s": 5,
            "personagens": [],
            "imagens_chave": [],
            "cenas": [{"idx": 1, "modo": "anim3d", "prompt_visual": "x", "narracao": "y", "duracao_s": 5}],
        })


def test_roteiro_cena_duracao_zero_falha():
    with pytest.raises(ValidationError):
        Roteiro.model_validate({
            "titulo": "x",
            "sinopse_curta": "y",
            "duracao_total_s": 5,
            "personagens": [],
            "imagens_chave": [],
            "cenas": [{"idx": 1, "modo": "t2v", "prompt_visual": "x", "narracao": "y", "duracao_s": 0}],
        })
