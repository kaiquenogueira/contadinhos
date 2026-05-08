"""Mapping publish_mode → privacy_status do YouTube (decisions §"Publish mode").

Função pura, testável sem dependência. Reutilizada por pipeline e CLI.
"""
from __future__ import annotations


# Decisions §Publish mode:
# - private_only      → 'private' (default Sprint 5; humano promove manual)
# - unlisted_review   → 'unlisted' (sobe unlisted, humano promove pra public)
# - direct_public     → 'public' (habilitar só após calibração)
_MAPPING: dict[str, str] = {
    "private_only": "private",
    "unlisted_review": "unlisted",
    "direct_public": "public",
}


def to_privacy_status(publish_mode: str) -> str:
    """Traduz `publish_mode` (config) pra `privacyStatus` da YouTube API."""
    if publish_mode not in _MAPPING:
        raise ValueError(
            f"publish_mode desconhecido: {publish_mode!r}. "
            f"Aceitos: {', '.join(_MAPPING)}."
        )
    return _MAPPING[publish_mode]


def valid_modes() -> set[str]:
    return set(_MAPPING)
