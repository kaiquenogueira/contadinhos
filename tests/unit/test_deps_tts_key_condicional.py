"""_real_deps() não deve exigir ELEVENLABS_API_KEY quando o TTS é OpenAI/Gemini.

Fix do bloqueador da Sprint 5b: a key do TTS é condicional ao
`config/providers.yaml::tts.provider`, não mais incondicional.
"""

from __future__ import annotations

import pytest

import contadinhos.core.config as cfg_mod
from contadinhos.core.tts.openai import OpenAITTS
from contadinhos.frontends.cli.deps import build_deps


def _isolate_env(monkeypatch):
    # env explícito + sem depender de .env real
    monkeypatch.setattr("contadinhos.frontends.cli.deps._ensure_env_loaded", lambda: None)
    monkeypatch.setenv("OPENAI_API_KEY", "k-openai")
    monkeypatch.setenv("GOOGLE_GENERATIVE_AI_API_KEY", "k-google")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("CONTADINHOS_FAKES", raising=False)


def test_real_deps_nao_exige_elevenlabs_quando_provider_openai(monkeypatch):
    _isolate_env(monkeypatch)
    # config real já traz tts.provider=openai (Fase A) — sem patch
    deps = build_deps(use_fakes=False)
    assert isinstance(deps.tts, OpenAITTS)


def test_real_deps_exige_key_do_provider_ativo(monkeypatch):
    _isolate_env(monkeypatch)
    orig = cfg_mod.load_config
    monkeypatch.setattr(
        cfg_mod,
        "load_config",
        lambda name, *a, **k: (
            {"tts": {"provider": "elevenlabs"}} if name == "providers" else orig(name, *a, **k)
        ),
    )
    with pytest.raises(RuntimeError, match="ELEVENLABS_API_KEY"):
        build_deps(use_fakes=False)
