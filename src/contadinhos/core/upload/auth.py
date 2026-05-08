"""OAuth desktop flow + token storage pra YouTube Data API v3.

Token e client_secret vivem em `~/.contadinhos/` (XDG-style, fora do repo).
Sprint 5 #35.
"""
from __future__ import annotations

from pathlib import Path

# Mínimo necessário pra videos.insert + leitura de status do canal
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def config_dir() -> Path:
    """`~/.contadinhos/` — criado on-demand."""
    p = Path.home() / ".contadinhos"
    p.mkdir(parents=True, exist_ok=True)
    return p


def client_secret_path() -> Path:
    return config_dir() / "client_secret.json"


def token_path() -> Path:
    return config_dir() / "youtube_token.json"


def load_credentials():
    """Tenta carregar token existente; refresh silencioso se expirado.

    Retorna `Credentials` válido ou `None` se token ausente / refresh falhou.
    Sempre persiste de volta após refresh bem-sucedido.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    tp = token_path()
    if not tp.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(tp), SCOPES)
    if creds.valid:
        return creds
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)
            return creds
        except Exception:
            return None
    return None


def save_credentials(creds) -> None:
    token_path().write_text(creds.to_json())


def run_oauth_flow():
    """Fluxo interativo InstalledApp (browser local).

    Lê `client_secret.json` de `~/.contadinhos/`. Levanta `FileNotFoundError`
    com mensagem clara se ausente.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    cs = client_secret_path()
    if not cs.exists():
        raise FileNotFoundError(
            f"client_secret.json ausente em {cs}. "
            "Crie um OAuth 2.0 Client ID tipo Desktop em "
            "https://console.cloud.google.com/apis/credentials e baixe o JSON "
            f"pra {cs}."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(cs), SCOPES)
    creds = flow.run_local_server(port=0)
    save_credentials(creds)
    return creds


def require_credentials():
    """Carrega credentials válidas; falha clara se ausentes / expiradas.

    Usado pelo `YouTubeUploader.upload()` em runtime — orienta o usuário a
    rodar `contadinhos auth-youtube` se token não existir.
    """
    creds = load_credentials()
    if creds is None or not creds.valid:
        raise RuntimeError(
            "credentials YouTube ausentes ou inválidas. "
            f"Rode `contadinhos auth-youtube` (token vai pra {token_path()})."
        )
    return creds
