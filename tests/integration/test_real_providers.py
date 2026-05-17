"""Smoke real-provider — opt-in via marker `real_provider` (custo $).

Skip por default; rode com:

    uv run pytest -m real_provider -v

Pré-condições: `.env` com `OPENAI_API_KEY` e `GOOGLE_GENERATIVE_AI_API_KEY`.
ElevenLabs descartada (Sprint 5b) — TTS smoke roda OpenAI + Gemini.
Custos por execução completa:

- transcribe (OpenAI): ~$0.02 (silêncio 30s)
- script (gpt-5-mini): ~$0.005
- pre_gate (gemini-2.5-flash): ~$0.01 (em crédito Google)
- nano_banana (4 candidatas): ~$0.16 (em crédito Google)
- tts openai (gpt-4o-mini-tts, ~5 palavras): ~$0.001
- tts gemini (2.5-flash-tts): ~$0.001 (em crédito Google)

Veo NÃO entra aqui — caro demais ($30+/run). Smoke manual em
`docs/sprint3-smoke.md`.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from contadinhos.core.images.nano_banana import NanoBananaImageGenerator
from contadinhos.core.policy.post_gate import GeminiPostGate
from contadinhos.core.policy.pre_gate import GeminiPreGateAuditor
from contadinhos.core.schemas import Roteiro
from contadinhos.core.script.openai_roteirista import OpenAIRoteirista
from contadinhos.core.transcribe import OpenAITranscriber
from contadinhos.core.tts.gemini import GeminiTTS
from contadinhos.core.tts.openai import OpenAITTS


def _load_env_once():
    from dotenv import load_dotenv

    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")


def _require(env_var: str) -> str:
    _load_env_once()
    val = os.environ.get(env_var)
    if not val:
        pytest.skip(f"{env_var} ausente — pulando real_provider")
    return val


@pytest.mark.real_provider
def test_real_transcribe_silencio(silencio_30s_m4a):
    """Transcribe áudio de silêncio. Aceita string vazia ou ruído leve."""
    key = _require("OPENAI_API_KEY")
    t = OpenAITranscriber(api_key=key, model="gpt-4o-mini-transcribe")
    text = t.transcribe(silencio_30s_m4a)
    assert isinstance(text, str)


@pytest.mark.real_provider
def test_real_roteirista_minimo():
    """gpt-5-mini gera Roteiro válido contra schema."""
    key = _require("OPENAI_API_KEY")
    r = OpenAIRoteirista(api_key=key)
    roteiro = r.generate(
        transcript="Era uma vez uma raposa que encontrou uma flor cantante no jardim.",
        target_duration_s=60,
    )
    assert isinstance(roteiro, Roteiro)
    assert len(roteiro.cenas) >= 3
    assert roteiro.sinopse_curta


@pytest.mark.real_provider
def test_real_pre_gate_aprova_roteiro_inocente(roteiro_minimo):
    """Pré-gate sobre roteiro acolhedor → verdict ok."""
    key = _require("GOOGLE_GENERATIVE_AI_API_KEY")
    auditor = GeminiPreGateAuditor(api_key=key)
    pc = auditor.audit(roteiro_minimo)
    assert pc.verdict in {"ok", "review_required"}


@pytest.mark.real_provider
@pytest.mark.slow
def test_real_nano_banana_gera_imagem(tmp_path):
    """Nano Banana gera 1 PNG válido. Custo: ~$0.04."""
    key = _require("GOOGLE_GENERATIVE_AI_API_KEY")
    g = NanoBananaImageGenerator(api_key=key)
    out = g.generate(
        prompt="raposinha laranja brincando num jardim ensolarado",
        n=1,
        output_dir=tmp_path,
    )
    assert len(out) == 1
    assert out[0].exists()
    # PNG signature
    assert out[0].read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.real_provider
def test_real_openai_tts_curto(tmp_path):
    """OpenAI gpt-4o-mini-tts — texto curto. Custo: ~$0.001.

    Verifica que: 1) responde sem erro 2) WAV válido (RIFF header).
    """
    key = _require("OPENAI_API_KEY")
    tts = OpenAITTS(api_key=key)
    out = tts.synthesize(
        text="Olá, eu sou a Clarinha.",
        voice_id="default",
        output_path=tmp_path / "smoke_openai.wav",
    )
    assert out.exists()
    assert out.stat().st_size > 1000
    assert out.read_bytes()[:4] == b"RIFF"


@pytest.mark.real_provider
def test_real_gemini_tts_curto(tmp_path):
    """Gemini 2.5 Flash TTS — texto curto. Custo: ~$0.001 (crédito Google).

    Valida o envelope PCM→WAV contra o output real do Gemini.
    """
    key = _require("GOOGLE_GENERATIVE_AI_API_KEY")
    tts = GeminiTTS(api_key=key)
    out = tts.synthesize(
        text="Olá, eu sou a Clarinha.",
        voice_id="default",
        output_path=tmp_path / "smoke_gemini.wav",
    )
    assert out.exists()
    assert out.stat().st_size > 1000
    assert out.read_bytes()[:4] == b"RIFF"


@pytest.mark.real_provider
@pytest.mark.slow
def test_real_post_gate_video_pequeno(placeholder_mp4):
    """Pós-gate sobre placeholder MP4 (5s). Custo: ~$0.05.

    Não validamos verdict específico — placeholder pode ou não disparar
    flags. Só checamos que o auditor consegue: 1) upload Files API
    2) processing → ACTIVE 3) parse JSON do output.
    """
    key = _require("GOOGLE_GENERATIVE_AI_API_KEY")
    p = GeminiPostGate(api_key=key)
    pc = p.audit(placeholder_mp4)
    assert pc.verdict in {"ok", "review_required"}
    assert pc.severity in {"low", "medium", "high"}
