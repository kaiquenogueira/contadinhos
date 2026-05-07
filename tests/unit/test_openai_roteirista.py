"""Testes unit do OpenAIRoteirista (sem rede).

Caminho real (chama API paga) fica em tests com marker `real_provider`.
"""
from __future__ import annotations

from contadinhos.core.script.openai_roteirista import OpenAIRoteirista, render_prompt


def test_render_prompt_substitui_placeholders():
    out = render_prompt("Era uma vez...", target_duration_s=75)
    assert "Era uma vez..." in out
    assert "75" in out
    assert "{{TRANSCRIPT}}" not in out
    assert "{{TARGET_DURATION_S}}" not in out


def test_construtor_usa_gpt5_mini_por_default():
    r = OpenAIRoteirista(api_key="fake-key")
    assert r.model == "gpt-5-mini"
    assert r._client is None


def test_construtor_aceita_override_model():
    r = OpenAIRoteirista(api_key="fake-key", model="gpt-5")
    assert r.model == "gpt-5"
