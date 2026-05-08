# Sprint 3 — Smoke real-provider manual

Os providers reais Sprint 3 são exercitados de duas formas:

## 1. Suite automática (opt-in via marker)

```bash
uv run pytest -m real_provider -v
```

Cobre transcribe, script, pre_gate e Nano Banana (1 imagem). Custo total
por execução: **~$0.04 out-of-pocket + ~$0.05 em crédito Google**. Pula
silenciosamente se a key não está no `.env`.

## 2. Veo 3.1 — só smoke manual (caro: $5–$10 por clipe de 8s)

Veo **não roda em CI nem em `pytest -m real_provider`**. Smoke manual:

```bash
# 1) export keys
source .env  # ou cargá-las pelo shell

# 2) rodar Python interativo
uv run python -c "
from contadinhos.core.video.veo import Veo31VideoGenerator
import os
v = Veo31VideoGenerator(api_key=os.environ['GOOGLE_GENERATIVE_AI_API_KEY'])
out = v.generate(
    prompt='paisagem aquarela: jardim com flores ao amanhecer',
    duration_s=5,
    output_path='/tmp/veo_smoke.mp4',
)
print('vídeo em:', out)
"
```

Espera-se um MP4 de 5s, ~2–4 MB, formato H.264.

Após smoke OK, abrir a story `2026-MM-DD-smoke-veo` e marcar no `cost_ledger.json`.

## 3. End-to-end completo (texto + imagem real, vídeo Fake)

Exercita o pipeline ponta-a-ponta com texto/imagem reais e Fakes pra TTS/post_gate/upload e **ainda Fake pro vídeo** (forçar via env):

```bash
# inserir uma story já com audio.m4a real (ou silêncio)
uv run contadinhos run stories/<id>
# para em pick_images — escolha humana via:
uv run contadinhos pick stories/<id> raposa --candidate 1
uv run contadinhos run stories/<id>  # continua até final.mp4
```

Custo: ~$0.04 + ~$0.50 em crédito (Nano Banana × N personagens × 4 candidatas).
