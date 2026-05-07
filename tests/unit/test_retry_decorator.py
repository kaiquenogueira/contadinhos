import httpx
import pytest

from contadinhos.core.providers.exceptions import ProviderError
from contadinhos.core.providers.retry import retryable


def _make_503_response():
    return httpx.Response(503, request=httpx.Request("GET", "https://x"))


def _make_400_response():
    return httpx.Response(400, request=httpx.Request("GET", "https://x"))


def test_retry_em_503_tres_vezes():
    calls = {"n": 0}

    @retryable(provider="test", base_delay_s=0)  # zero delay no teste
    def fn():
        calls["n"] += 1
        raise httpx.HTTPStatusError("503", request=_make_503_response().request, response=_make_503_response())

    with pytest.raises(ProviderError) as exc:
        fn()
    assert calls["n"] == 3
    assert exc.value.provider == "test"
    assert exc.value.attempt == 3


def test_no_retry_em_400():
    calls = {"n": 0}

    @retryable(provider="test", base_delay_s=0)
    def fn():
        calls["n"] += 1
        raise httpx.HTTPStatusError("400", request=_make_400_response().request, response=_make_400_response())

    with pytest.raises(ProviderError):
        fn()
    assert calls["n"] == 1  # não retentou


def test_sucesso_na_primeira():
    calls = {"n": 0}

    @retryable(provider="test", base_delay_s=0)
    def fn():
        calls["n"] += 1
        return "ok"

    assert fn() == "ok"
    assert calls["n"] == 1


def test_retry_em_connect_error():
    calls = {"n": 0}

    @retryable(provider="test", base_delay_s=0)
    def fn():
        calls["n"] += 1
        raise httpx.ConnectError("network down")

    with pytest.raises(ProviderError):
        fn()
    assert calls["n"] == 3


def test_sucesso_na_segunda_tentativa():
    calls = {"n": 0}

    @retryable(provider="test", base_delay_s=0)
    def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("flaky")
        return "ok"

    assert fn() == "ok"
    assert calls["n"] == 2
