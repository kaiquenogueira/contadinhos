"""Wiring de providers — Sprint 1 só tem Fakes.

Sprints 2+ trocam o `_real_deps()` pelos providers reais conforme cada
um for implementado.
"""
from __future__ import annotations

import os

from contadinhos.core.pipeline import PipelineDeps


def _project_root():
    from pathlib import Path

    p = Path(__file__).resolve()
    for ancestor in p.parents:
        if (ancestor / "pyproject.toml").exists():
            return ancestor
    raise RuntimeError("pyproject.toml não encontrado a partir de " + str(p))


def _fake_deps() -> PipelineDeps:
    # Imports locais — Fakes vivem em tests/, não devem ser carregados
    # em modo real (provoca erro se tests/ for podada do deploy).
    import sys

    project_root = _project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from tests.fakes.fake_post_gate import FakePostGate
    from tests.fakes.fake_pre_gate import FakePreGateAuditor
    from tests.fakes.fake_image_generator import FakeImageGenerator
    from tests.fakes.fake_roteirista import FakeRoteirista
    from tests.fakes.fake_transcriber import FakeTranscriber
    from tests.fakes.fake_tts import FakeTTS
    from tests.fakes.fake_video_generator import FakeVideoGenerator
    from tests.fakes.fake_youtube_uploader import FakeYouTubeUploader

    return PipelineDeps(
        transcriber=FakeTranscriber(),
        roteirista=FakeRoteirista(),
        pre_gate=FakePreGateAuditor(),
        image_generator=FakeImageGenerator(),
        video_generator=FakeVideoGenerator(),
        tts=FakeTTS(),
        post_gate=FakePostGate(),
        youtube_uploader=FakeYouTubeUploader(),
    )


def _real_deps() -> PipelineDeps:
    raise NotImplementedError(
        "Providers reais ainda não implementados (Sprints 2+). "
        "Use --with-fakes ou env CONTADINHOS_FAKES=1."
    )


def build_deps(use_fakes: bool) -> PipelineDeps:
    """Monta `PipelineDeps`. Lê env `CONTADINHOS_FAKES` como fallback."""
    if use_fakes or os.environ.get("CONTADINHOS_FAKES") == "1":
        return _fake_deps()
    return _real_deps()
