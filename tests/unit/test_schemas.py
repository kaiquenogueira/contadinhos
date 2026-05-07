import pytest
from pydantic import ValidationError

from contadinhos.core.schemas import PolicyCheck, Roteiro


def test_roteiro_minimo_valida(roteiro_minimo_dict):
    roteiro = Roteiro.model_validate(roteiro_minimo_dict)
    assert roteiro.titulo == "A raposa curiosa"
    assert len(roteiro.cenas) == 2
    assert roteiro.sinopse_curta


def test_roteiro_completo_valida(roteiro_completo_dict):
    roteiro = Roteiro.model_validate(roteiro_completo_dict)
    assert len(roteiro.cenas) == 10


def test_roteiro_sem_cenas_falha(fixtures_dir):
    import json
    raw = json.loads((fixtures_dir / "roteiros" / "invalido_sem_cenas.json").read_text())
    with pytest.raises(ValidationError):
        Roteiro.model_validate(raw)


def test_policy_check_default_ok():
    pc = PolicyCheck()
    assert pc.verdict == "ok"
    assert pc.flags == []


def test_policy_check_review_required_aceita_flags():
    pc = PolicyCheck(
        verdict="review_required",
        severity="high",
        flags=[{"category": "violencia", "description": "lobo persegue", "scene_idx": 1}],
    )
    assert pc.verdict == "review_required"
    assert len(pc.flags) == 1
    assert pc.flags[0].category == "violencia"


def test_cena_modo_invalido_falha():
    with pytest.raises(ValidationError):
        Roteiro.model_validate({
            "titulo": "x",
            "sinopse_curta": "y",
            "duracao_total_s": 5,
            "personagens": [],
            "imagens_chave": [],
            "cenas": [{"idx": 1, "modo": "invalid_mode", "prompt_visual": "x", "narracao": "y", "duracao_s": 5}],
            "policy_check": {"verdict": "ok", "severity": "low", "flags": []},
        })


def test_sinopse_curta_obrigatoria():
    with pytest.raises(ValidationError):
        Roteiro.model_validate({
            "titulo": "x",
            "duracao_total_s": 5,
            "personagens": [],
            "imagens_chave": [],
            "cenas": [{"idx": 1, "modo": "t2v", "prompt_visual": "x", "narracao": "y", "duracao_s": 5}],
            "policy_check": {"verdict": "ok", "severity": "low", "flags": []},
        })
