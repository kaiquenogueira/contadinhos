"""Unit tests do GeminiPostGate (sem rede)."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from contadinhos.core.policy.post_gate import GeminiPostGate
from contadinhos.core.schemas import PolicyCheck


def test_construtor_default():
    p = GeminiPostGate(api_key="fake-key")
    assert p.model == "gemini-2.5-flash"
    assert p._client is None


def test_audit_arquivo_inexistente_levanta(tmp_path):
    p = GeminiPostGate(api_key="fake-key")
    with pytest.raises(FileNotFoundError):
        p.audit(tmp_path / "missing.mp4")


def _fake_file_obj(state_name: str = "ACTIVE", name: str = "files/abc"):
    return SimpleNamespace(
        name=name,
        state=SimpleNamespace(name=state_name),
    )


def test_audit_upload_e_call_modelo(tmp_path, placeholder_mp4):
    captured: dict = {"deleted": []}

    class _FakeFiles:
        def upload(self, *, file):
            captured["uploaded"] = file
            return _fake_file_obj()

        def get(self, *, name):
            return _fake_file_obj(name=name)

        def delete(self, *, name):
            captured["deleted"].append(name)

    class _FakeModels:
        def generate_content(self, *, model, contents):
            captured["model"] = model
            captured["contents_types"] = [type(c).__name__ for c in contents]
            return SimpleNamespace(
                text='{"verdict": "ok", "severity": "low", "flags": []}'
            )

    class _FakeClient:
        def __init__(self):
            self.files = _FakeFiles()
            self.models = _FakeModels()

    p = GeminiPostGate(api_key="fake-key")
    p._client = _FakeClient()

    pc = p.audit(placeholder_mp4)
    assert isinstance(pc, PolicyCheck)
    assert pc.verdict == "ok"
    # MP4 foi enviado pra Files API
    assert captured["uploaded"] == str(placeholder_mp4)
    # cleanup chamado
    assert captured["deleted"] == ["files/abc"]


def test_audit_review_required_é_parseado(placeholder_mp4):
    raw = (
        '{"verdict": "review_required", "severity": "high", '
        '"flags": [{"category": "glitch_visual", '
        '"description": "rosto distorcido em 0:08", "scene_idx": 2}]}'
    )

    class _FakeFiles:
        def upload(self, *, file):
            return _fake_file_obj()

        def delete(self, *, name):
            pass

    class _FakeModels:
        def generate_content(self, *, model, contents):
            return SimpleNamespace(text=raw)

    class _FakeClient:
        def __init__(self):
            self.files = _FakeFiles()
            self.models = _FakeModels()

    p = GeminiPostGate(api_key="fake-key")
    p._client = _FakeClient()

    pc = p.audit(placeholder_mp4)
    assert pc.verdict == "review_required"
    assert len(pc.flags) == 1
    assert pc.flags[0].category == "glitch_visual"
    assert pc.flags[0].scene_idx == 2


def test_audit_categoria_invalida_levanta(placeholder_mp4):
    """Schema-fechado: categoria fora do enum é erro."""
    import pydantic

    class _FakeFiles:
        def upload(self, *, file):
            return _fake_file_obj()

        def delete(self, *, name):
            pass

    class _FakeModels:
        def generate_content(self, *, model, contents):
            return SimpleNamespace(
                text='{"verdict": "review_required", "severity": "low", '
                '"flags": [{"category": "racismo", "description": "x"}]}'
            )

    class _FakeClient:
        def __init__(self):
            self.files = _FakeFiles()
            self.models = _FakeModels()

    p = GeminiPostGate(api_key="fake-key")
    p._client = _FakeClient()

    with pytest.raises((pydantic.ValidationError, Exception)) as exc_info:
        p.audit(placeholder_mp4)
    # ProviderError pode wrapper o ValidationError; ambos são aceitáveis
    assert "racismo" in str(exc_info.value).lower() or "validation" in str(exc_info.value).lower()


def test_wait_for_active_processa_upload_em_andamento(placeholder_mp4, monkeypatch):
    """Files.upload retorna PROCESSING; polla até ACTIVE."""
    monkeypatch.setattr("contadinhos.core.policy.post_gate.time.sleep", lambda _s: None)
    state = {"calls": 0}

    class _FakeFiles:
        def upload(self, *, file):
            return _fake_file_obj(state_name="PROCESSING", name="files/p1")

        def get(self, *, name):
            state["calls"] += 1
            if state["calls"] >= 2:
                return _fake_file_obj(state_name="ACTIVE", name=name)
            return _fake_file_obj(state_name="PROCESSING", name=name)

        def delete(self, *, name):
            pass

    class _FakeModels:
        def generate_content(self, *, model, contents):
            return SimpleNamespace(
                text='{"verdict": "ok", "severity": "low", "flags": []}'
            )

    class _FakeClient:
        def __init__(self):
            self.files = _FakeFiles()
            self.models = _FakeModels()

    p = GeminiPostGate(api_key="fake-key")
    p._client = _FakeClient()
    # patch sleep pra teste rápido
    import contadinhos.core.policy.post_gate as m

    p.audit(placeholder_mp4)
    assert state["calls"] >= 2
