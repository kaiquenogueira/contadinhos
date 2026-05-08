"""Testes unit do NanoBananaImageGenerator (sem rede)."""
from __future__ import annotations

from pathlib import Path

import pytest

from contadinhos.core.images.nano_banana import NanoBananaImageGenerator


def test_construtor_usa_modelo_nano_banana_por_default():
    g = NanoBananaImageGenerator(api_key="fake-key")
    assert g.model == "gemini-3.1-flash-image-preview"
    assert g._client is None


def test_construtor_aceita_override_model():
    g = NanoBananaImageGenerator(api_key="fake-key", model="gemini-2.5-flash-image")
    assert g.model == "gemini-2.5-flash-image"


def test_aborta_em_prompt_vazio(tmp_path):
    g = NanoBananaImageGenerator(api_key="fake-key")
    with pytest.raises(ValueError):
        g.generate(prompt="", n=4, output_dir=tmp_path)


def test_aplica_style_guide_no_prompt(tmp_path, monkeypatch):
    """Style aquarela é prepended antes da chamada API."""
    captured: dict = {}

    class _FakeModels:
        def generate_content(self, *, model, contents, config=None):
            captured["contents"] = contents
            # mimica resposta com 1 inline image
            from types import SimpleNamespace
            part = SimpleNamespace(
                inline_data=SimpleNamespace(data=b"\x89PNG\r\n\x1a\nfake")
            )
            return SimpleNamespace(
                candidates=[SimpleNamespace(content=SimpleNamespace(parts=[part]))]
            )

    class _FakeClient:
        def __init__(self):
            self.models = _FakeModels()

    g = NanoBananaImageGenerator(api_key="fake-key")
    g._client = _FakeClient()
    g.generate(prompt="raposa correndo", n=1, output_dir=tmp_path)
    assert "aquarela" in captured["contents"].lower()
    assert "raposa correndo" in captured["contents"]


def test_gera_n_arquivos_e_retorna_paths(tmp_path):
    """N candidatas → N candidate_*.png escritos em disco."""
    from types import SimpleNamespace

    class _FakeModels:
        def generate_content(self, *, model, contents, config=None):
            part = SimpleNamespace(
                inline_data=SimpleNamespace(data=b"\x89PNG\r\n\x1a\nfake")
            )
            return SimpleNamespace(
                candidates=[SimpleNamespace(content=SimpleNamespace(parts=[part]))]
            )

    class _FakeClient:
        def __init__(self):
            self.models = _FakeModels()

    g = NanoBananaImageGenerator(api_key="fake-key")
    g._client = _FakeClient()
    out = g.generate(prompt="x", n=4, output_dir=tmp_path)
    assert len(out) == 4
    for i, p in enumerate(out):
        assert Path(p).name == f"candidate_{i}.png"
        assert Path(p).exists()
        assert Path(p).read_bytes().startswith(b"\x89PNG")
