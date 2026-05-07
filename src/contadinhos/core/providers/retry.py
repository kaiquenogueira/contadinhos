"""Retry decorator único pra todos os providers (§8.8 de `docs/decisions.md`).

3 tentativas, exponential backoff (1s, 4s, 16s) com jitter ±25%, só retenta
em 5xx, ConnectError, ReadTimeout. 4xx falha imediato. Gates (verdict
review_required) NÃO são erro — não passar pelo decorator.
"""
from __future__ import annotations

import functools
import random
import time
from collections.abc import Callable
from typing import TypeVar

import httpx

from contadinhos.core.providers.exceptions import ProviderError


T = TypeVar("T")

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BASE_DELAY_S = 1.0
DEFAULT_JITTER = 0.25
DEFAULT_RETRYABLE_STATUS = {500, 502, 503, 504}


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in DEFAULT_RETRYABLE_STATUS
    if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout)):
        return True
    return False


def retryable(
    provider: str,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_delay_s: float = DEFAULT_BASE_DELAY_S,
    jitter: float = DEFAULT_JITTER,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator de retry com exponential backoff."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if not _is_retryable(exc):
                        raise ProviderError(provider, attempt, exc) from exc
                    if attempt >= max_attempts:
                        raise ProviderError(provider, attempt, exc) from exc
                    delay = base_delay_s * (4 ** (attempt - 1))
                    if jitter and delay > 0:
                        delay *= 1 + random.uniform(-jitter, jitter)
                    if delay > 0:
                        time.sleep(delay)
            # inalcançável
            raise ProviderError(provider, max_attempts, last_exc or RuntimeError("unknown"))

        return wrapper

    return decorator
