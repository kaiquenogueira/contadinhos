"""Testa wiring de _real_deps() (não chama API)."""
from __future__ import annotations

import os

import pytest

from contadinhos.frontends.cli.deps import _real_deps, build_deps


def test_real_deps_requer_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_GENERATIVE_AI_API_KEY", "fake")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake")
    monkeypatch.setattr(
        "contadinhos.frontends.cli.deps._ensure_env_loaded", lambda: None
    )
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        _real_deps()


def test_real_deps_requer_google_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    monkeypatch.delenv("GOOGLE_GENERATIVE_AI_API_KEY", raising=False)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake")
    monkeypatch.setattr(
        "contadinhos.frontends.cli.deps._ensure_env_loaded", lambda: None
    )
    with pytest.raises(RuntimeError, match="GOOGLE_GENERATIVE_AI_API_KEY"):
        _real_deps()


def test_real_deps_requer_elevenlabs_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    monkeypatch.setenv("GOOGLE_GENERATIVE_AI_API_KEY", "fake")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setattr(
        "contadinhos.frontends.cli.deps._ensure_env_loaded", lambda: None
    )
    with pytest.raises(RuntimeError, match="ELEVENLABS_API_KEY"):
        _real_deps()


def test_real_deps_constroi_providers_reais(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    monkeypatch.setenv("GOOGLE_GENERATIVE_AI_API_KEY", "fake-google")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-eleven")
    monkeypatch.setattr(
        "contadinhos.frontends.cli.deps._ensure_env_loaded", lambda: None
    )
    deps = _real_deps()
    # types correctos sem precisar conectar
    assert deps.transcriber.__class__.__name__ == "OpenAITranscriber"
    assert deps.roteirista.__class__.__name__ == "OpenAIRoteirista"
    assert deps.pre_gate.__class__.__name__ == "GeminiPreGateAuditor"
    assert deps.image_generator.__class__.__name__ == "NanoBananaImageGenerator"
    assert deps.video_generator.__class__.__name__ == "Veo31VideoGenerator"
    assert deps.tts.__class__.__name__ == "ElevenLabsTTS"
    # Sprint 5 ainda Fake
    assert deps.post_gate.__class__.__name__ == "FakePostGate"
    assert deps.youtube_uploader.__class__.__name__ == "FakeYouTubeUploader"


def test_build_deps_com_fakes_nao_le_env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GENERATIVE_AI_API_KEY", raising=False)
    deps = build_deps(use_fakes=True)
    assert deps.transcriber.__class__.__name__ == "FakeTranscriber"
