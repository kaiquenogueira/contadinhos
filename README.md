# contadinhos

Pipeline pessoal pra transformar histórias improvisadas (contadas pra filha
de ~3 anos) em vídeos animados anônimos via IA generativa, publicados no
YouTube como conteúdo "made for kids".

> Projeto pessoal, não empresarial. Saída anônima por design — sem voz do
> pai, sem aparência da filha real. Personagem-menininha fictícia (Clarinha)
> gerada por IA.

## Documentação

Ler nesta ordem:

| Documento | O quê |
|---|---|
| [`docs/decisions.md`](./docs/decisions.md) | **Por quê.** Cada decisão de design (escopo, ferramentas, custo, política, identidade) com motivação explícita. |
| [`docs/sprints.md`](./docs/sprints.md) | **Como.** Plano de execução em 8 sprints (Sprint 0 pré-flight → Sprint 7 calibração). Checkboxes, DoD, dependências. |
| [`CONTEXT.md`](./CONTEXT.md) | **Glossário** de termos do domínio. Vocabulário canônico que decisões/sprints/código devem honrar. |

## Estado atual

Projeto em **Sprint 0 — Pré-flight** (operacional, parcial).
Próxima sprint: **Sprint 1 — Foundations** (bootstrap do repo).

Ver [`docs/sprints.md#estado-atual`](./docs/sprints.md#estado-atual) pra
detalhes correntes.

## Stack

- Python 3.12+ via `uv`
- Pipeline core (`src/contadinhos/core/`) headless; frontends plugáveis
  (`src/contadinhos/frontends/{cli,telegram}/`)
- Veo 3.1 (`lite` em dev / `fast` em produção) padrão de geração de vídeo +
  Nano Banana 2 (`gemini-3.1-flash-image-preview`) pra imagens-chave + TTS
  via OpenAI `gpt-4o-mini-tts` (default Sprint 5b) ou Gemini 2.5 Flash TTS +
  ffmpeg pra montagem + `gpt-4o-transcribe` STT + GPT-5 mini roteirista +
  Gemini 2.5 Flash multimodal pós-gate
- YouTube Data API v3 pra upload + made-for-kids
- Backup via `rclone` pro Google Drive

Detalhes em [`docs/decisions.md`](./docs/decisions.md).

## Backup / restore

```bash
# Backup (configurado em launchctl, 1×/dia)
rclone sync ~/contadinhos drive:Backup/contadinhos \
  --backup-dir drive:Backup/contadinhos.versions/$(date +%Y%m%d) \
  --exclude-from .rcloneignore

# Restore (em outra máquina ou após desastre)
rclone sync drive:Backup/contadinhos ~/contadinhos --exclude-from .rcloneignore
# Depois: uv venv && uv sync && rodar OAuth de novo
```

Mais detalhes em [`docs/decisions.md`](./docs/decisions.md) §14.
