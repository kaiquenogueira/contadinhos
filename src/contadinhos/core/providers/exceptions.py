"""Exceções tipadas dos providers."""
from __future__ import annotations


class ProviderError(Exception):
    """Erro final após retries esgotados (§8.8 de `docs/decisions.md`)."""

    def __init__(self, provider: str, attempt: int, original: Exception):
        self.provider = provider
        self.attempt = attempt
        self.original = original
        super().__init__(f"provider={provider} attempt={attempt} original={original!r}")
