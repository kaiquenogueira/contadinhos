# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é

Pipeline pessoal que transforma histórias improvisadas (áudio) em vídeos
animados anônimos via IA generativa, publicados no YouTube como conteúdo
"made for kids". Saída anônima por design — personagem fictícia (Clarinha),
sem voz/imagem reais.

## Documentação como fonte de verdade

Ler nesta ordem antes de mudanças não-triviais:

- **`docs/decisions.md`** — o **porquê** de cada decisão (escopo, ferramentas,
  custo, política, identidade). Seções numeradas (§N) referenciadas direto nos
  docstrings do código.
- **`docs/sprints.md`** — o **como**: plano em sprints, DoD, dependências.
  A seção "Estado atual" pode estar atrasada em relação ao `git log` — confie
  no histórico de commits pra saber o que de fato foi entregue.
- **`CONTEXT.md`** — glossário canônico. Termos em commits/prompts/código
  devem casar com ele (Roteiro, Cena, I2V/T2V, Policy check, Story, etc.).

`docs/decisions.md` §20 ("Harness engineering + TDD") é o critério explícito
de aceitação de PR — a tabela "regra de ouro" em §20.1 lista invariantes que
não devem ser quebradas silenciosamente. Se uma feature quebra uma linha
dela, levantar a questão antes de implementar.

## Comandos

```bash
uv sync                                    # instala deps (Python 3.12+, gerenciado por uv)
uv run pytest -m "not slow and not real_provider"   # loop rápido (default, sem rede)
uv run pytest -m "not real_provider"       # pré-PR (inclui slow, sem custo $)
uv run pytest -m real_provider tests/integration/test_real_*.py  # smoke real ($$, manual antes do DoD)
uv run pytest tests/unit/test_story_io.py::test_next_action_progressao -q  # um teste
uv run ruff check . && uv run ruff format --check .  # lint + format

# CLI (entrypoint: contadinhos.frontends.cli.main:app)
uv run contadinhos new "slug-da-historia"
uv run contadinhos run stories/2026-05-16-slug --with-fakes   # E2E sem custo
uv run contadinhos status stories/2026-05-16-slug
uv run contadinhos auth-youtube                                # OAuth desktop, 1×
```

- **`ffmpeg`/`ffprobe`** são dependência de sistema (montagem em
  `core/assemble/ffmpeg.py` via subprocess) — não vêm via `uv`.
- `--with-fakes` (ou env `CONTADINHOS_FAKES=1`) troca todos os providers
  pelos Fakes em `tests/fakes/`; em modo Fakes o `run` ativa `--auto-pick`
  automaticamente (pula a escolha humana de imagem).
- Markers de pytest declarados em `pyproject.toml`: `integration`,
  `real_provider` (skipado por default via `addopts`), `slow`.

## Arquitetura

**Core headless + frontends plugáveis.** `src/contadinhos/core/` é uma
biblioteca pura que **nunca** importa `frontends/`. Frontends
(`frontends/cli/`, `frontends/telegram/`) montam os deps e chamam o core.
Adicionar frontend = novo módulo, zero alteração no core.

**Filesystem-as-state.** Não há banco. Toda a unidade de trabalho é uma
`Story` = um diretório `stories/<YYYY-MM-DD>-<slug>/`. O estado é o conjunto
de arquivos presentes. `core/story.py::Story.next_action()` calcula a próxima
etapa olhando quais arquivos existem — é o contrato de status que CLI/Telegram
leem. Qualquer comando é resumível: reentrar = no-op ou re-aproveita.

**Pipeline = funções puras sobre uma Story.** `core/pipeline.py` tem uma
função por etapa (`run_transcribe`, `run_script`, `run_images`, `run_video`,
`run_tts`, `run_assemble`, `run_publish`) e `run_all` que itera o
`next_action` até `done`. Ordem:
`new → transcribe → script → images → pick_images → video → tts → assemble → policy_post → publish → done`.
`pick_images` é uma parada humana (escolher 1 de N candidatas de imagem-chave)
— `run_all` para aí salvo `auto_pick=True`.

**Injeção de providers via `PipelineDeps`.** As funções de etapa recebem um
dataclass `PipelineDeps` (bag de providers) — nunca importam impls
concretas. `frontends/cli/deps.py::build_deps` monta `_real_deps()` (lê keys
de `.env`) ou `_fake_deps()`. Os Fakes vivem em `tests/fakes/` e só são
importados em modo fake (imports locais), pra não acoplar core a `tests/`.

**Contrato entre etapas = Roteiro JSON.** `core/schemas.py` define os
schemas pydantic (`Roteiro`, `Cena`, `ImagemChave`, `PolicyCheck`). Toda
etapa downstream é função pura sobre esse JSON. Mudar o schema é mudar o
contrato — atualizar fakes/fixtures/contract tests junto.

**Provider-agnostic onde a troca é cara.** Vídeo (`core/video/base.py`),
imagem (`core/images/base.py`), TTS (`core/tts/base.py`), gates
(`core/policy/`), upload (`core/upload/base.py`) têm interface em `base.py`
e impls plugáveis (Veo, Nano Banana, ElevenLabs, Gemini, YouTube). Provider
default escolhido em `config/providers.yaml`.

**Gate duplo, bloqueio sem auto-retry.** Pré-gate (texto, depois do
roteirista, **chamada LLM separada** pra evitar conflito de interesse) e
pós-gate (multimodal sobre o MP4 final). `verdict=review_required` levanta
`pipeline.PipelineBlocked` → para o pipeline, abre revisão humana, **sem
retry automático**. Snapshots `policy_check_pre.json`/`policy_check_post.json`
são audit trail imutável.

**Config isolada da lógica.** Tudo que evolui com aprendizado (modelos,
prompts, thresholds, categorias, vozes, teto de custo, templates) mora em
`config/*.yaml` e prompts em `config/prompts/*.md`. Carregado **só** via
`core/config.py::load_config(name)` — config **nunca** é importada como
módulo Python. Secrets só em `.env` (ver `.env.example`). Ao adicionar um
valor que pode mudar, ponha em YAML, não hardcode.

**Custo rastreado por story.** `core/budget.py` mantém `cost_ledger.json`
append-only em cada story (`step`, `provider`, `cost_usd`, `paid_via`).
Soma dos ledgers do mês = custo mensal vs teto.

**Resiliência de providers.** Decorator único `core/providers/retry.py`
(`@retryable`): 3 tentativas, backoff exponencial (1s/4s/16s) + jitter,
retenta só em 5xx/ConnectError/Timeout; 4xx falha imediato. Gates
(`review_required`) **não** são erro — não passam pelo decorator. Lock
advisory por story via `Story.lock()` (`fcntl.flock`, não-blocking).

## Convenções de teste

- **Contract tests compartilhados** (`tests/contracts/<interface>.py`): uma
  classe abstrata de asserções subclassada **tanto pelo Fake quanto pelo
  Real** — mesmo teste roda nos dois. Ao adicionar/mudar uma interface,
  atualize o contract test (não só o caso concreto).
- **Fakes são test doubles completos, não mocks.** Implementam a interface
  inteira (não só os métodos chamados). Nada de `MagicMock` — esconde
  contrato quebrado. Cada `*Provider`/`*Generator` do core tem Fake
  correspondente em `tests/fakes/`.
- **Auth Google:** uma única `GOOGLE_GENERATIVE_AI_API_KEY` (Gemini API
  direta, não Vertex/ADC) atende Veo + Nano Banana + Gemini multimodal
  (pré/pós-gate). OpenAI key cobre STT + roteirista; ElevenLabs key cobre TTS.

## TDD por feature (decisions §20.2)

Toda feature substancial entra via red-green-refactor (mover linha de config
fica fora). Primeiro teste é sempre o **caminho feliz E2E com Fakes**
(integração antes de unit). Um teste = uma asserção principal; nome descreve
comportamento, não método. Não testar wrappers triviais de SDK, layout de
YAML, nem strings de prompt (são dado → fixture, não asserção). Não
generalizar além do que o teste exige.
