"""Funções puras de pipeline: cada etapa é uma função sobre uma Story.

Etapas recebem providers via injeção (não importam impls) — frontends
montam o `PipelineDeps` e passam pra cá.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from contadinhos.core.assemble.ffmpeg import concat_clips
from contadinhos.core.schemas import Roteiro
from contadinhos.core.story import Story


@dataclass
class PipelineDeps:
    """Bag de providers injetados por frontend."""

    transcriber: object  # implementa .transcribe(audio_path) -> str
    roteirista: object  # implementa .generate(transcript, target_duration_s) -> Roteiro
    pre_gate: object  # implementa .audit(roteiro) -> PolicyCheck
    image_generator: object  # implementa .generate(prompt, n, output_dir) -> [Path]
    video_generator: object  # implementa .generate(prompt, duration_s, output_path, first_frame=) -> Path
    tts: object  # implementa .synthesize(text, voice_id, output_path) -> Path
    post_gate: object  # implementa .audit(video_path) -> PolicyCheck
    youtube_uploader: object  # implementa .upload(...) -> dict


def run_transcribe(story: Story, deps: PipelineDeps) -> Path:
    audio = story.path / "audio.m4a"
    if not audio.exists():
        raise FileNotFoundError(f"audio.m4a ausente em {story.path}")
    text = deps.transcriber.transcribe(audio)
    out = story.path / "transcript.txt"
    out.write_text(text)
    return out


def run_script(story: Story, deps: PipelineDeps, target_duration_s: float = 75) -> Roteiro:
    transcript = (story.path / "transcript.txt").read_text()
    roteiro = deps.roteirista.generate(transcript=transcript, target_duration_s=target_duration_s)
    # pré-gate como chamada separada (§7.1)
    policy = deps.pre_gate.audit(roteiro)
    roteiro.policy_check = policy
    story.write_roteiro(roteiro)
    return roteiro


def run_images(story: Story, deps: PipelineDeps, candidatos: int = 4) -> None:
    """Gera N candidatas por personagem; primeira candidata vira `chosen.png`.

    Sprint 1 não tem UX de escolha humana — primeira sempre escolhida.
    Sprint 3 substitui pela escolha real via CLI/Telegram.
    """
    roteiro = story.read_roteiro()
    for img in roteiro.imagens_chave:
        out_dir = story.path / "images" / img.id
        candidatas = deps.image_generator.generate(
            prompt=img.prompt, n=candidatos, output_dir=out_dir
        )
        # Sprint 1: primeira como escolha (TODO Sprint 3: prompt humano)
        chosen = out_dir / "chosen.png"
        chosen.write_bytes(candidatas[0].read_bytes())


def run_video(story: Story, deps: PipelineDeps) -> None:
    roteiro = story.read_roteiro()
    clips_dir = story.path / "clips"
    clips_dir.mkdir(exist_ok=True)
    for cena in roteiro.cenas:
        out = clips_dir / f"scene_{cena.idx:02d}.mp4"
        first_frame = None
        if cena.modo == "i2v" and cena.imagem_chave_ref:
            first_frame = story.path / "images" / cena.imagem_chave_ref / "chosen.png"
        deps.video_generator.generate(
            prompt=cena.prompt_visual,
            duration_s=cena.duracao_s,
            output_path=out,
            first_frame=first_frame,
        )


def run_tts(story: Story, deps: PipelineDeps, voice_id: str = "default") -> None:
    roteiro = story.read_roteiro()
    audio_dir = story.path / "audio"
    audio_dir.mkdir(exist_ok=True)
    for cena in roteiro.cenas:
        out = audio_dir / f"narration_{cena.idx:02d}.wav"
        deps.tts.synthesize(text=cena.narracao, voice_id=voice_id, output_path=out)


def run_assemble(story: Story, deps: PipelineDeps) -> Path:
    roteiro = story.read_roteiro()
    return concat_clips(roteiro, story.path)


def run_publish(story: Story, deps: PipelineDeps, publish_mode: str = "private_only") -> dict:
    roteiro = story.read_roteiro()
    final = story.path / "final.mp4"
    # pós-gate
    policy = deps.post_gate.audit(final)
    (story.path / "policy_check_post.json").write_text(policy.model_dump_json(indent=2))
    if policy.verdict == "review_required":
        raise RuntimeError(f"pós-gate bloqueou: {policy.flags}")
    # upload
    title = f"{roteiro.titulo} | contadinhos"
    description = f"{roteiro.titulo}\n\n{roteiro.sinopse_curta}"
    result = deps.youtube_uploader.upload(
        video_path=final,
        title=title,
        description=description,
        tags=["historiainfantil", "aquarela"],
        made_for_kids=True,
        privacy_status="private" if publish_mode == "private_only" else "unlisted",
    )
    (story.path / "upload_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def run_all(story: Story, deps: PipelineDeps) -> None:
    """Roda etapas a partir do `next_action` da story até `done`.

    Resumível: invocar 2× é seguro — pula etapas já feitas.
    """
    while True:
        action = story.next_action()
        if action == "new":
            raise FileNotFoundError(f"story sem audio.m4a em {story.path}")
        if action == "transcribe":
            run_transcribe(story, deps)
        elif action == "script":
            run_script(story, deps)
        elif action == "images":
            run_images(story, deps)
        elif action == "video":
            run_video(story, deps)
        elif action == "tts":
            run_tts(story, deps)
        elif action == "assemble":
            run_assemble(story, deps)
        elif action == "policy_post":
            roteiro = story.read_roteiro()
            policy = deps.post_gate.audit(story.path / "final.mp4")
            (story.path / "policy_check_post.json").write_text(policy.model_dump_json(indent=2))
            if policy.verdict == "review_required":
                raise RuntimeError(f"pós-gate bloqueou: {policy.flags}")
        elif action == "publish":
            run_publish(story, deps)
        elif action == "done":
            return
        else:
            raise RuntimeError(f"next_action desconhecida: {action}")
