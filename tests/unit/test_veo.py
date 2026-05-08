"""Testes unit do Veo31VideoGenerator (sem rede)."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from contadinhos.core.video.veo import Veo31VideoGenerator


def test_construtor_usa_modelo_veo_por_default():
    v = Veo31VideoGenerator(api_key="fake-key")
    assert v.model == "veo-3.1-generate-preview"
    assert v._client is None


def test_construtor_aceita_override_model():
    v = Veo31VideoGenerator(api_key="fake-key", model="veo-3.1-fast-generate-preview")
    assert v.model == "veo-3.1-fast-generate-preview"


def test_aborta_em_prompt_vazio(tmp_path):
    v = Veo31VideoGenerator(api_key="fake-key")
    with pytest.raises(ValueError):
        v.generate(prompt="", duration_s=5, output_path=tmp_path / "x.mp4")


def _fake_operation_done(video_bytes: bytes = b"\x00\x00\x00\x18ftypmp42fake"):
    """Mock de operation que já vem .done=True com video inline."""
    video = SimpleNamespace(video_bytes=video_bytes, uri=None)
    gv = SimpleNamespace(video=video)
    result = SimpleNamespace(generated_videos=[gv])
    return SimpleNamespace(done=True, result=result, error=None)


def test_t2v_gera_mp4(tmp_path):
    captured: dict = {}

    class _FakeModels:
        def generate_videos(self, *, model, source, config=None):
            captured["model"] = model
            captured["source"] = source
            captured["config"] = config
            return _fake_operation_done()

    class _FakeClient:
        def __init__(self):
            self.models = _FakeModels()

    v = Veo31VideoGenerator(api_key="fake-key")
    v._client = _FakeClient()
    out = v.generate(
        prompt="paisagem aquarela",
        duration_s=5,
        output_path=tmp_path / "scene.mp4",
    )
    assert out.exists()
    assert out.read_bytes().startswith(b"\x00\x00\x00\x18ftyp")
    # style aplicado
    assert "aquarela" in captured["source"].prompt.lower()
    # i2v não setado (T2V puro)
    assert captured["source"].image is None


def test_i2v_envia_first_frame(tmp_path, placeholder_png):
    captured: dict = {}

    class _FakeModels:
        def generate_videos(self, *, model, source, config=None):
            captured["source"] = source
            return _fake_operation_done()

    class _FakeClient:
        def __init__(self):
            self.models = _FakeModels()

    v = Veo31VideoGenerator(api_key="fake-key")
    v._client = _FakeClient()
    out = v.generate(
        prompt="raposa caminhando",
        duration_s=5,
        first_frame=placeholder_png,
        output_path=tmp_path / "scene_i2v.mp4",
    )
    assert out.exists()
    # source.image carrega bytes do PNG
    assert captured["source"].image is not None
    assert captured["source"].image.image_bytes is not None
    assert captured["source"].image.mime_type == "image/png"


def test_polling_aguarda_operation_concluir(tmp_path):
    """Operation começa not-done, fica done na 2ª tentativa."""
    state = {"calls": 0}

    class _FakeOps:
        def get(self, op):
            state["calls"] += 1
            if state["calls"] >= 2:
                return _fake_operation_done()
            return SimpleNamespace(done=False, result=None, error=None)

    class _FakeModels:
        def generate_videos(self, *, model, source, config=None):
            return SimpleNamespace(done=False, result=None, error=None)

    class _FakeClient:
        def __init__(self):
            self.models = _FakeModels()
            self.operations = _FakeOps()

    v = Veo31VideoGenerator(api_key="fake-key", poll_interval_s=0.0)
    v._client = _FakeClient()
    out = v.generate(prompt="x", duration_s=5, output_path=tmp_path / "x.mp4")
    assert out.exists()
    assert state["calls"] >= 2


def test_operation_com_erro_levanta(tmp_path):
    class _FakeModels:
        def generate_videos(self, *, model, source, config=None):
            return SimpleNamespace(
                done=True,
                result=None,
                error={"code": 13, "message": "internal"},
            )

    class _FakeClient:
        def __init__(self):
            self.models = _FakeModels()

    from contadinhos.core.providers.exceptions import ProviderError

    v = Veo31VideoGenerator(api_key="fake-key")
    v._client = _FakeClient()
    with pytest.raises(ProviderError, match="veo"):
        v.generate(prompt="x", duration_s=5, output_path=tmp_path / "x.mp4")
