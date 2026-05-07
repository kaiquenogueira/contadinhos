"""Pipeline grava cost_ledger.json em cada etapa (decisions §11.3, §15).

Roda transcribe→script (que internamente chama pre_gate) com Fakes.
Verifica que o ledger nasce com os 3 itens esperados.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from contadinhos.core import pipeline
from contadinhos.core.budget import read_ledger, total_out_of_pocket
from contadinhos.core.story import Story


@pytest.fixture
def story_com_audio(tmp_path, silencio_30s_m4a) -> Story:
    base = tmp_path / "stories"
    base.mkdir()
    story = Story.create(slug="ledger-test", base_dir=base, today=date(2026, 5, 7))
    (story.path / "audio.m4a").write_bytes(silencio_30s_m4a.read_bytes())
    return story


@pytest.fixture
def deps_fake():
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


@pytest.mark.integration
def test_transcribe_e_script_populam_ledger(story_com_audio, deps_fake):
    pipeline.run_transcribe(story_com_audio, deps_fake)
    pipeline.run_script(story_com_audio, deps_fake, target_duration_s=75)

    ledger = read_ledger(story_com_audio)
    steps = [item["step"] for item in ledger["items"]]
    assert steps == ["transcribe", "script", "pre_gate"]
    # paid_via correto por etapa
    by_step = {item["step"]: item for item in ledger["items"]}
    assert by_step["transcribe"]["paid_via"] == "out_of_pocket"
    assert by_step["script"]["paid_via"] == "out_of_pocket"
    assert by_step["pre_gate"]["paid_via"] == "google_credits"
    # snapshot do pré-gate gravado
    assert (story_com_audio.path / "policy_check_pre.json").exists()


@pytest.mark.integration
def test_total_out_of_pocket_ignora_credits(story_com_audio, deps_fake):
    pipeline.run_transcribe(story_com_audio, deps_fake)
    pipeline.run_script(story_com_audio, deps_fake)
    total = total_out_of_pocket(story_com_audio)
    # transcribe (0.018) + script (0.005); pre_gate é google_credits
    assert total == pytest.approx(0.023, rel=1e-3)


@pytest.mark.integration
def test_pre_gate_review_required_levanta_pipeline_blocked(
    story_com_audio, deps_fake, monkeypatch
):
    """Quando pre_gate retorna review_required, run_script bloqueia."""
    from contadinhos.core.schemas import PolicyCheck, PolicyCheckFlag

    flagged = PolicyCheck(
        verdict="review_required",
        severity="high",
        flags=[PolicyCheckFlag(category="medo", description="x")],
    )
    monkeypatch.setattr(deps_fake.pre_gate, "audit", lambda _r: flagged)

    pipeline.run_transcribe(story_com_audio, deps_fake)
    with pytest.raises(pipeline.PipelineBlocked):
        pipeline.run_script(story_com_audio, deps_fake)
    # ledger ainda assim deve ter os 3 itens (custo já incorrido)
    ledger = read_ledger(story_com_audio)
    assert len(ledger["items"]) == 3
