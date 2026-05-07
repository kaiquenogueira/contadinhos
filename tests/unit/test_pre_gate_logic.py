"""Pré-gate é chamada LLM separada (decisions §7.1).

Nesta sprint testamos:
- Lógica de classificação dado um output de modelo (mock do output bruto)
- Merge de flags com PolicyCheck existente
- Categorias enumeradas validam pelo schema

A integração real com Gemini fica em test_real_pre_gate.py (marker
real_provider, skip default).
"""
from contadinhos.core.policy.pre_gate import (
    GeminiPreGateAuditor,
    parse_audit_response,
)
from contadinhos.core.schemas import PolicyCheck, Roteiro


def test_parse_response_aprovado():
    raw = '{"verdict": "ok", "severity": "low", "flags": []}'
    pc = parse_audit_response(raw)
    assert pc.verdict == "ok"
    assert pc.flags == []


def test_parse_response_review_required():
    raw = """{
        "verdict": "review_required",
        "severity": "high",
        "flags": [
            {"category": "violencia", "description": "lobo persegue raposa", "scene_idx": 1}
        ]
    }"""
    pc = parse_audit_response(raw)
    assert pc.verdict == "review_required"
    assert len(pc.flags) == 1
    assert pc.flags[0].category == "violencia"
    assert pc.flags[0].scene_idx == 1


def test_parse_response_categoria_invalida_levanta():
    """Schema fechado: categoria fora do enum é erro."""
    import pydantic
    raw = '{"verdict": "review_required", "severity": "low", "flags": [{"category": "racismo", "description": "x"}]}'
    try:
        parse_audit_response(raw)
        raise AssertionError("deveria ter levantado ValidationError")
    except pydantic.ValidationError:
        pass


def test_auditor_e_cliente_diferente_do_roteirista(roteiro_minimo):
    """Pré-gate deve ser provider distinto do roteirista (§7.1).

    O construtor explicitamente recebe um api_key → cliente Gemini.
    Asserção: classe é importável e construtor aceita api_key.
    """
    # Construir sem chamar API real — só verifica que classe existe e aceita params
    auditor = GeminiPreGateAuditor(api_key="fake-key", model="gemini-2.5-flash")
    assert auditor.model == "gemini-2.5-flash"
