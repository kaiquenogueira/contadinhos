"""Funções puras de pipeline: cada etapa é uma função sobre uma Story.

Etapas recebem providers via injeção (não importam impls) — frontends
montam o `PipelineDeps` e passam pra cá.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from contadinhos.core.assemble.ffmpeg import concat_clips, validate_final
from contadinhos.core.budget import append_ledger_entry
from contadinhos.core.config import load_config
from contadinhos.core.schemas import Roteiro
from contadinhos.core.story import Story


class PipelineBlocked(RuntimeError):
    """Gate (pré ou pós) bloqueou — abre revisão humana, sem auto-retry."""


def _provider_id(provider: object, fallback: str) -> str:
    return getattr(provider, "model", None) or fallback


def _step_cost(step: str) -> tuple[float, str]:
    """Estimativa nominal por etapa + paid_via, lida de `config/budget.yaml`.

    Sprint 2 usa estimativas fixas (decisions §6); Sprint 7 troca por leitura
    de `response.usage` real. Mini-first: valores baixos por default.
    """
    cfg = load_config("budget").get("step_estimates", {})
    entry = cfg.get(step, {})
    return float(entry.get("cost_usd", 0.0)), entry.get("paid_via", "out_of_pocket")


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
    cost, paid_via = _step_cost("transcribe")
    append_ledger_entry(
        story=story,
        step="transcribe",
        provider=_provider_id(deps.transcriber, "fake"),
        cost_usd=cost,
        paid_via=paid_via,
    )
    return out


def run_script(story: Story, deps: PipelineDeps, target_duration_s: float = 75) -> Roteiro:
    transcript = (story.path / "transcript.txt").read_text()
    roteiro = deps.roteirista.generate(transcript=transcript, target_duration_s=target_duration_s)
    cost_s, paid_s = _step_cost("script")
    append_ledger_entry(
        story=story,
        step="script",
        provider=_provider_id(deps.roteirista, "fake"),
        cost_usd=cost_s,
        paid_via=paid_s,
    )
    # pré-gate como chamada separada (§7.1) — provider distinto do roteirista
    policy = deps.pre_gate.audit(roteiro)
    cost_g, paid_g = _step_cost("pre_gate")
    append_ledger_entry(
        story=story,
        step="pre_gate",
        provider=_provider_id(deps.pre_gate, "fake"),
        cost_usd=cost_g,
        paid_via=paid_g,
    )
    roteiro.policy_check = policy
    story.write_roteiro(roteiro)
    # snapshot separado pro audit trail (§16)
    (story.path / "policy_check_pre.json").write_text(policy.model_dump_json(indent=2))
    if policy.verdict == "review_required":
        raise PipelineBlocked(
            f"pré-gate bloqueou story={story.path.name} flags={policy.flags}"
        )
    return roteiro


def run_images(story: Story, deps: PipelineDeps, candidatos: int = 4) -> None:
    """Gera N candidatas por personagem (decisions §13 fase 3).

    **Não** cria `chosen.png` — escolha humana via `core.images.picker.pick_candidate`
    (subcomando CLI `pick`). `next_action` retorna `pick_images` enquanto
    candidatas existem mas chosen falta.
    """
    roteiro = story.read_roteiro()
    n_imagens = 0
    for img in roteiro.imagens_chave:
        out_dir = story.path / "images" / img.id
        # idempotente: se já há candidatas, não regera
        if (out_dir / "candidate_0.png").exists():
            continue
        deps.image_generator.generate(
            prompt=img.prompt, n=candidatos, output_dir=out_dir
        )
        n_imagens += 1
    if n_imagens > 0:
        cost, paid_via = _step_cost("images")
        append_ledger_entry(
            story=story,
            step="images",
            provider=_provider_id(deps.image_generator, "fake"),
            cost_usd=cost * n_imagens,
            paid_via=paid_via,
            qty=n_imagens * candidatos,
        )


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


def run_assemble(story: Story, deps: PipelineDeps, validate: bool = False) -> Path:
    """Mix narração + concat clips em `final.mp4`.

    `validate=True` chama `validate_final` (ffprobe) — útil em modo real, mas
    Fakes não casam duração de placeholders então default é off.
    """
    roteiro = story.read_roteiro()
    final = concat_clips(roteiro, story.path)
    if validate:
        expected_duration = sum(c.duracao_s for c in roteiro.cenas)
        validate_final(final, expected_duration_s=expected_duration, tolerance_s=2.0)
    return final


def run_publish(story: Story, deps: PipelineDeps, publish_mode: str = "private_only") -> dict:
    roteiro = story.read_roteiro()
    final = story.path / "final.mp4"
    # pós-gate
    policy = deps.post_gate.audit(final)
    (story.path / "policy_check_post.json").write_text(policy.model_dump_json(indent=2))
    if policy.verdict == "review_required":
        raise PipelineBlocked(f"pós-gate bloqueou: {policy.flags}")
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


def run_all(story: Story, deps: PipelineDeps, auto_pick: bool = False) -> None:
    """Roda etapas a partir do `next_action` da story até `done`.

    Resumível: invocar 2× é seguro — pula etapas já feitas.

    `auto_pick=True` (modo dev/test) escolhe automaticamente `candidate_0.png`
    como `chosen.png`. Default False — humano-in-loop, para em `pick_images`.
    """
    from contadinhos.core.images.picker import pick_candidate

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
        elif action == "pick_images":
            if not auto_pick:
                return  # humano-in-loop: para aqui pra escolha manual
            roteiro = story.read_roteiro()
            for img in roteiro.imagens_chave:
                if not (story.path / "images" / img.id / "chosen.png").exists():
                    pick_candidate(story, img.id, candidate_idx=0)
        elif action == "video":
            run_video(story, deps)
        elif action == "tts":
            run_tts(story, deps)
        elif action == "assemble":
            run_assemble(story, deps)
        elif action == "policy_post":
            policy = deps.post_gate.audit(story.path / "final.mp4")
            (story.path / "policy_check_post.json").write_text(policy.model_dump_json(indent=2))
            if policy.verdict == "review_required":
                raise PipelineBlocked(f"pós-gate bloqueou: {policy.flags}")
        elif action == "publish":
            run_publish(story, deps)
        elif action == "done":
            return
        else:
            raise RuntimeError(f"next_action desconhecida: {action}")
