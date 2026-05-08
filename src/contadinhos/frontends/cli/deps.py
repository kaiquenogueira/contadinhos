"""Wiring de providers.

Sprint 3: `_real_deps()` monta providers reais lendo keys de `.env` via
python-dotenv. Fakes continuam disponíveis via `--with-fakes` ou env
`CONTADINHOS_FAKES=1`.
"""
from __future__ import annotations

import os

from contadinhos.core.pipeline import PipelineDeps


_DOTENV_LOADED = False


def _ensure_env_loaded() -> None:
    """Carrega .env da raiz do projeto na 1ª invocação. Idempotente."""
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    from dotenv import load_dotenv
    project_root = _project_root()
    load_dotenv(project_root / ".env")
    _DOTENV_LOADED = True


def _require_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(
            f"variável de ambiente {key} não definida. "
            f"Adicione em .env ou exporte no shell."
        )
    return val


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
    """Monta providers reais.

    Sprint 3 cobre transcribe/script/pre_gate/images/video. TTS/post_gate/upload
    ainda Fake até Sprints 4–5.
    """
    _ensure_env_loaded()
    openai_key = _require_env("OPENAI_API_KEY")
    google_key = _require_env("GOOGLE_GENERATIVE_AI_API_KEY")

    from contadinhos.core.images.nano_banana import NanoBananaImageGenerator
    from contadinhos.core.policy.pre_gate import GeminiPreGateAuditor
    from contadinhos.core.script.openai_roteirista import OpenAIRoteirista
    from contadinhos.core.transcribe import OpenAITranscriber
    from contadinhos.core.video.veo import Veo31VideoGenerator

    # Fakes ainda em uso pra etapas Sprints 4–5
    import sys

    project_root = _project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from tests.fakes.fake_post_gate import FakePostGate
    from tests.fakes.fake_tts import FakeTTS
    from tests.fakes.fake_youtube_uploader import FakeYouTubeUploader

    return PipelineDeps(
        transcriber=OpenAITranscriber(api_key=openai_key),
        roteirista=OpenAIRoteirista(api_key=openai_key),
        pre_gate=GeminiPreGateAuditor(api_key=google_key),
        image_generator=NanoBananaImageGenerator(api_key=google_key),
        video_generator=Veo31VideoGenerator(api_key=google_key),
        tts=FakeTTS(),
        post_gate=FakePostGate(),
        youtube_uploader=FakeYouTubeUploader(),
    )


def build_deps(use_fakes: bool) -> PipelineDeps:
    """Monta `PipelineDeps`. Lê env `CONTADINHOS_FAKES` como fallback."""
    if use_fakes or os.environ.get("CONTADINHOS_FAKES") == "1":
        return _fake_deps()
    return _real_deps()
