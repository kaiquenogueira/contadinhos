"""Validação real do assemble: final.mp4 tem audio + video + duração ok."""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from contadinhos.core import pipeline
from contadinhos.core.assemble.ffmpeg import probe_streams, validate_final
from contadinhos.core.story import Story


def _ffmpeg_disponivel() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


pytestmark = pytest.mark.skipif(
    not _ffmpeg_disponivel(), reason="ffmpeg/ffprobe não instalados"
)


def _deps_fakes():
    from contadinhos.core.pipeline import PipelineDeps
    from tests.fakes.fake_image_generator import FakeImageGenerator
    from tests.fakes.fake_post_gate import FakePostGate
    from tests.fakes.fake_pre_gate import FakePreGateAuditor
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


@pytest.fixture
def story_pronta_pra_assemble(tmp_path, silencio_30s_m4a) -> Story:
    """Story após transcribe→script→images→pick→video→tts."""
    base = tmp_path / "stories"
    base.mkdir()
    story = Story.create(slug="assemble-test", base_dir=base, today=date(2026, 5, 8))
    (story.path / "audio.m4a").write_bytes(silencio_30s_m4a.read_bytes())
    deps = _deps_fakes()
    pipeline.run_transcribe(story, deps)
    pipeline.run_script(story, deps)
    pipeline.run_images(story, deps)
    # auto-pick pra teste
    from contadinhos.core.images.picker import pick_candidate
    roteiro = story.read_roteiro()
    for img in roteiro.imagens_chave:
        pick_candidate(story, img.id, candidate_idx=0)
    pipeline.run_video(story, deps)
    pipeline.run_tts(story, deps)
    return story


@pytest.mark.integration
def test_final_mp4_tem_video_e_audio(story_pronta_pra_assemble):
    final = pipeline.run_assemble(story_pronta_pra_assemble, _deps_fakes())
    streams = probe_streams(final)
    types = {s["codec_type"] for s in streams}
    assert "video" in types
    assert "audio" in types, "final.mp4 deve ter trilha de áudio (narração mixada)"


@pytest.mark.integration
def test_validate_final_aprova_arquivo_ok(story_pronta_pra_assemble):
    """Validação aceita o arquivo gerado quando duração esperada é a observada."""
    final = pipeline.run_assemble(story_pronta_pra_assemble, _deps_fakes())
    # Fakes geram duração curta — usa duração real como referência
    from contadinhos.core.assemble.ffmpeg import probe_duration
    observed = probe_duration(final)
    validate_final(final, expected_duration_s=observed, tolerance_s=0.5)


@pytest.mark.integration
def test_validate_final_falha_se_arquivo_curto(story_pronta_pra_assemble):
    """Se duração observada < esperada - tolerância → erro."""
    final = pipeline.run_assemble(story_pronta_pra_assemble, _deps_fakes())
    with pytest.raises(RuntimeError, match="dura"):
        validate_final(final, expected_duration_s=10_000.0, tolerance_s=0.5)


@pytest.mark.integration
def test_validate_final_falha_se_sem_audio(tmp_path):
    """final.mp4 silencioso (sem trilha de áudio) → erro."""
    silent = tmp_path / "silent.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=black:s=320x240:d=2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(silent),
        ],
        check=True,
    )
    with pytest.raises(RuntimeError, match="audio"):
        validate_final(silent, expected_duration_s=2.0, tolerance_s=0.5)
