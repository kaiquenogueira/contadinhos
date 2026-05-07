"""Schemas pydantic do roteiro JSON e policy_check.

Contrato canônico entre etapas do pipeline (§3.1, §7.4 de `docs/decisions.md`).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Personagem(BaseModel):
    id: str
    descricao_visual: str


class ImagemChave(BaseModel):
    id: str
    prompt: str


class Cena(BaseModel):
    idx: int = Field(ge=1)
    modo: Literal["i2v", "t2v"]
    imagem_chave_ref: str | None = None
    prompt_visual: str
    narracao: str
    duracao_s: float = Field(gt=0)


class PolicyCheckFlag(BaseModel):
    category: Literal[
        "medo",
        "violencia",
        "tema_adulto",
        "linguagem",
        "glitch_visual",
        "vibe_sombria",
        "outro",
    ]
    description: str
    scene_idx: int | None = None


class PolicyCheck(BaseModel):
    verdict: Literal["ok", "review_required"] = "ok"
    severity: Literal["low", "medium", "high"] = "low"
    flags: list[PolicyCheckFlag] = Field(default_factory=list)
    reviewer_note: str | None = None


class Roteiro(BaseModel):
    titulo: str
    sinopse_curta: str
    duracao_total_s: float
    personagens: list[Personagem]
    imagens_chave: list[ImagemChave]
    cenas: list[Cena]
    policy_check: PolicyCheck = Field(default_factory=PolicyCheck)

    @field_validator("cenas")
    @classmethod
    def cenas_nao_vazias(cls, v: list[Cena]) -> list[Cena]:
        if not v:
            raise ValueError("roteiro deve ter pelo menos uma cena")
        return v
