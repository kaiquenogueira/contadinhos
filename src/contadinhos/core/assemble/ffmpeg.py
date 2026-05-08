"""Montagem do final.mp4 via ffmpeg.

Mix de narração (`audio/narration_NN.wav`) com cada clipe de cena
(`clips/scene_NN.mp4`) → concat tudo em `final.mp4`. Validação via ffprobe
garante que o resultado tem `video` + `audio` e duração próxima da soma das
`duracao_s`. Música/legenda ficam pra Sprint 4.5+.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from contadinhos.core.schemas import Roteiro


def _run_ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _mix_scene(
    video_path: Path, narration_path: Path, output_path: Path
) -> Path:
    """Adiciona narração como trilha de áudio do clipe da cena.

    Vídeo é re-encoded só se preciso (preserva codec); áudio vira AAC pra
    compatibilidade com concat. Cuts no menor (`-shortest`) pra evitar
    travamento se narração for mais longa que o clipe.
    """
    _run_ffmpeg([
        "-i", str(video_path),
        "-i", str(narration_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path),
    ])
    return output_path


def concat_clips(roteiro: Roteiro, story_path: Path) -> Path:
    """Mix narração em cada cena → concat em `final.mp4`.

    Sprint 4: substitui a versão silenciosa da Sprint 1. `audio/narration_NN.wav`
    é obrigatório por cena.
    """
    clips_dir = story_path / "clips"
    audio_dir = story_path / "audio"
    output = story_path / "final.mp4"

    cenas_ordenadas = sorted(roteiro.cenas, key=lambda c: c.idx)

    with tempfile.TemporaryDirectory(prefix="contadinhos_mix_", dir=story_path) as tmp_str:
        tmp_dir = Path(tmp_str)
        mixed_paths: list[Path] = []
        for cena in cenas_ordenadas:
            clip = clips_dir / f"scene_{cena.idx:02d}.mp4"
            narration = audio_dir / f"narration_{cena.idx:02d}.wav"
            if not clip.exists():
                raise FileNotFoundError(f"clip ausente: {clip}")
            if not narration.exists():
                raise FileNotFoundError(f"narração ausente: {narration}")
            mixed = tmp_dir / f"mixed_{cena.idx:02d}.mp4"
            _mix_scene(clip, narration, mixed)
            mixed_paths.append(mixed)

        list_path = tmp_dir / "concat.txt"
        list_path.write_text(
            "\n".join(f"file '{p.resolve()}'" for p in mixed_paths) + "\n"
        )
        _run_ffmpeg([
            "-f", "concat", "-safe", "0",
            "-i", str(list_path),
            "-c", "copy",
            str(output),
        ])

    return output


def probe_streams(video_path: Path) -> list[dict]:
    """ffprobe — retorna lista de streams com `codec_type` etc."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_streams", "-show_format",
            "-of", "json",
            str(video_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout).get("streams", [])


def probe_duration(video_path: Path) -> float:
    """Duração total em segundos (do container)."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(video_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    fmt = json.loads(result.stdout).get("format", {})
    return float(fmt.get("duration", 0.0))


def validate_final(
    video_path: Path,
    expected_duration_s: float,
    tolerance_s: float = 2.0,
) -> None:
    """Valida `final.mp4`: tem video + audio + duração ≈ esperada.

    Levanta `RuntimeError` com mensagem específica em caso de falha.
    """
    if not video_path.exists():
        raise RuntimeError(f"final.mp4 ausente: {video_path}")
    streams = probe_streams(video_path)
    types = {s["codec_type"] for s in streams}
    if "video" not in types:
        raise RuntimeError(f"final.mp4 sem stream de video: {video_path}")
    if "audio" not in types:
        raise RuntimeError(f"final.mp4 sem stream de audio: {video_path}")
    duration = probe_duration(video_path)
    if duration < expected_duration_s - tolerance_s:
        raise RuntimeError(
            f"duração do final.mp4 ({duration:.2f}s) < esperada "
            f"({expected_duration_s:.2f}s ± {tolerance_s}s)"
        )
