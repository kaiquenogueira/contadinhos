"""Unit tests pra OAuth helpers (sem rede, sem browser)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from contadinhos.core.upload import auth


def test_paths_em_home_contadinhos(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    p = auth.config_dir()
    assert p == tmp_path / ".contadinhos"
    assert p.exists()
    assert auth.client_secret_path() == p / "client_secret.json"
    assert auth.token_path() == p / "youtube_token.json"


def test_load_credentials_retorna_none_se_token_ausente(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert auth.load_credentials() is None


def test_run_oauth_flow_falha_se_client_secret_ausente(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(FileNotFoundError, match="client_secret"):
        auth.run_oauth_flow()


def test_require_credentials_orienta_user_se_ausente(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(RuntimeError, match="auth-youtube"):
        auth.require_credentials()


def test_save_persiste_token_no_arquivo(monkeypatch, tmp_path):
    """save_credentials grava JSON parseável em token_path."""
    monkeypatch.setenv("HOME", str(tmp_path))

    from google.oauth2.credentials import Credentials
    creds = Credentials(
        token="fake-access",
        refresh_token="fake-refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="fake-id",
        client_secret="fake-secret",
        scopes=auth.SCOPES,
    )
    auth.save_credentials(creds)
    assert auth.token_path().exists()
    raw = json.loads(auth.token_path().read_text())
    assert raw["refresh_token"] == "fake-refresh"
    assert raw["client_id"] == "fake-id"


def test_load_credentials_retorna_none_se_refresh_falha(monkeypatch, tmp_path):
    """Token expirado com refresh_token fake → tenta refresh → falha → None.

    Comportamento esperado em produção: caller chama require_credentials()
    que dá mensagem clara orientando o user a re-autenticar.
    """
    monkeypatch.setenv("HOME", str(tmp_path))

    from google.oauth2.credentials import Credentials
    creds = Credentials(
        token="fake-access",
        refresh_token="fake-refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="fake-id",
        client_secret="fake-secret",
        scopes=auth.SCOPES,
    )
    auth.save_credentials(creds)
    # refresh contra Google falha (creds são fakes) → None
    assert auth.load_credentials() is None
