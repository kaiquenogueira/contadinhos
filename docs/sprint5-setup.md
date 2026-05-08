# Sprint 5 — Setup manual antes do primeiro upload

Sprint 5 ativa o pós-gate multimodal e o upload real no YouTube.
**Antes de tudo isso funcionar**, alguns passos manuais que você (humano)
precisa fazer fora do código:

## 1. Habilitar APIs no Google Cloud (~3 min)

Mesmo projeto Google associado à `GOOGLE_GENERATIVE_AI_API_KEY` (memória
`project_google_auth`). Abra um por um:

- **YouTube Data API v3**:
  https://console.cloud.google.com/apis/library/youtube.googleapis.com
  → "Enable"
- **Generative Language API** (Gemini, se ainda não enabled —
  pendência da Sprint 3):
  https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
  → "Enable"

## 2. Configurar OAuth consent screen (~5 min)

https://console.cloud.google.com/apis/credentials/consent

- **User Type**: External
- **App name**: contadinhos
- **User support email**: plataformaencantrip@gmail.com
- **Audiences**: adicione `plataformaencantrip@gmail.com` como **Test user**
  (enquanto o app não estiver "verified" pelo Google, apenas test users
  conseguem usar — pra uso pessoal isso basta)
- **Scopes**: adicione manualmente
  - `https://www.googleapis.com/auth/youtube.upload`
  - `https://www.googleapis.com/auth/youtube.readonly`

Não submeta pra verification — uso pessoal, sem necessidade.

## 3. Criar OAuth 2.0 Client ID tipo Desktop (~1 min)

https://console.cloud.google.com/apis/credentials

- **Create credentials** → **OAuth client ID**
- **Application type**: Desktop app
- **Name**: contadinhos-cli (livre)
- Crie → baixe o JSON

## 4. Salvar `client_secret.json` em `~/.contadinhos/`

```bash
mkdir -p ~/.contadinhos
mv ~/Downloads/client_secret_*.json ~/.contadinhos/client_secret.json
chmod 600 ~/.contadinhos/client_secret.json
```

## 5. Garantir 2FA forte na conta Google

Antes do primeiro upload, https://myaccount.google.com/security →
2-Step Verification → ativar (preferencialmente com authenticator app, não
SMS). YouTube bloqueia uploads de canais kids sem 2FA.

## 6. Rodar OAuth flow uma vez

```bash
uv run contadinhos auth-youtube
```

Vai abrir o browser, você loga em `plataformaencantrip@gmail.com`, aprova
os escopos. Token vai pra `~/.contadinhos/youtube_token.json`. Em runs
subsequentes o pipeline refresca o access token automaticamente — você não
precisa repetir até o **refresh_token** expirar (Google: 6 meses sem uso,
ou se você revogar manualmente).

## 7. Smoke teste manual de upload (opcional, mas recomendo)

```bash
# crie uma story de teste com um final.mp4 qualquer
# ou aproveite uma story já completa
uv run python - <<'PY'
from pathlib import Path
from contadinhos.core.upload.youtube import YouTubeUploader

u = YouTubeUploader()
res = u.upload(
    video_path=Path("stories/<id>/final.mp4"),
    title="contadinhos — smoke teste (privado)",
    description="Teste, ignore.",
    tags=["test"],
    made_for_kids=True,
    privacy_status="private",
)
print(res)
PY
```

Vídeo aparece em https://studio.youtube.com como **privado**. Aprovar visualmente
e deletar.
