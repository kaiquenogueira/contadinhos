# Sprint 5 — Smoke real-provider manual

## 1. Suite automática (opt-in via marker)

```bash
uv run pytest -m real_provider -v
```

Cobre transcribe + script + pre_gate + nano_banana + tts + **post_gate**.
Custo total: **~$0.05 out-of-pocket + ~$0.20 em crédito Google** por
execução completa. Pula silenciosamente se key ausente.

## 2. Upload — só smoke manual (efeito colateral público)

Upload **não roda em pytest** mesmo com `-m real_provider` — cada execução
deixa rastro visível em https://studio.youtube.com. Smoke manual:

### 2.1. Pré-condições

- `~/.contadinhos/client_secret.json` existe (veja
  [sprint5-setup.md](sprint5-setup.md))
- `~/.contadinhos/youtube_token.json` existe (rodar `contadinhos
  auth-youtube` uma vez)
- Story com `final.mp4` válido pronta em `stories/<id>/`

### 2.2. Comando

```bash
# default = private_only (recomendado pro 1º upload)
uv run contadinhos publish stories/<id>
```

Ou explícito:

```bash
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

### 2.3. Validação

Vídeo aparece em https://studio.youtube.com como **privado**. Aprove
visualmente:

- ✅ thumbnail correta
- ✅ "Made for kids" marcado
- ✅ Título e descrição usam o template em `config/youtube.yaml`
- ✅ Tags presentes (`historiainfantil`, `aquarela`, ...)

Se algo der errado, **delete o vídeo de teste** antes de rodar de novo.

## 3. End-to-end com providers reais (custoso!)

```bash
uv run contadinhos run stories/<id>
# para em pick_images — escolha humana:
uv run contadinhos pick stories/<id> raposa --candidate 1
uv run contadinhos pick stories/<id> menininha --candidate 0
uv run contadinhos run stories/<id>  # continua até upload
```

Custo estimado por vídeo Sprint 5 completo (Veo + tudo): **~$30–55** (decisions §6).
**Não rode** sem ter calibrado os providers individualmente primeiro.
