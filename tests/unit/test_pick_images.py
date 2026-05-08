"""UX de escolha de imagem-chave (Sprint 3 #20, decisions §13 fase 3).

run_images deixa de copiar primeira candidata como chosen.png. Estado
intermediário pick_images aparece em next_action quando candidates existem
mas chosen.png falta. Subcomando pick consolida a escolha.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from contadinhos.core import pipeline
from contadinhos.core.images.picker import pick_candidate
from contadinhos.core.story import Story


@pytest.fixture
def story_pos_script(tmp_path, roteiro_completo_dict) -> Story:
    base = tmp_path / "stories"
    base.mkdir()
    story = Story.create(slug="pick-test", base_dir=base, today=date(2026, 5, 7))
    (story.path / "audio.m4a").write_text("dummy")
    (story.path / "transcript.txt").write_text("dummy")
    (story.path / "roteiro.json").write_text(json.dumps(roteiro_completo_dict))
    return story


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


def test_run_images_nao_cria_chosen_automaticamente(story_pos_script):
    pipeline.run_images(story_pos_script, _deps_fakes(), candidatos=4)
    roteiro = story_pos_script.read_roteiro()
    for img in roteiro.imagens_chave:
        img_dir = story_pos_script.path / "images" / img.id
        assert (img_dir / "candidate_0.png").exists()
        assert not (img_dir / "chosen.png").exists(), (
            f"chosen.png NÃO deve ser criado automático em {img.id} (Sprint 3)"
        )


def test_next_action_pick_images_quando_candidatos_sem_chosen(story_pos_script):
    pipeline.run_images(story_pos_script, _deps_fakes(), candidatos=4)
    assert story_pos_script.next_action() == "pick_images"


def test_pick_candidate_copia_para_chosen(story_pos_script):
    pipeline.run_images(story_pos_script, _deps_fakes(), candidatos=4)
    roteiro = story_pos_script.read_roteiro()
    img_id = roteiro.imagens_chave[0].id

    pick_candidate(story_pos_script, img_id, candidate_idx=2)

    chosen = story_pos_script.path / "images" / img_id / "chosen.png"
    candidate = story_pos_script.path / "images" / img_id / "candidate_2.png"
    assert chosen.exists()
    assert chosen.read_bytes() == candidate.read_bytes()


def test_pick_candidate_invalido_levanta(story_pos_script):
    pipeline.run_images(story_pos_script, _deps_fakes(), candidatos=4)
    roteiro = story_pos_script.read_roteiro()
    img_id = roteiro.imagens_chave[0].id

    with pytest.raises(FileNotFoundError):
        pick_candidate(story_pos_script, img_id, candidate_idx=99)


def test_next_action_avanca_para_video_apos_pick_completo(story_pos_script):
    pipeline.run_images(story_pos_script, _deps_fakes(), candidatos=4)
    roteiro = story_pos_script.read_roteiro()
    for img in roteiro.imagens_chave:
        pick_candidate(story_pos_script, img.id, candidate_idx=0)
    assert story_pos_script.next_action() == "video"
