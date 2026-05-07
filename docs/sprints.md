# contadinhos — plano de execução em sprints

> Documento de **execução** (o "como"). O **"por quê"** mora em
> [`decisions.md`](./decisions.md). Sempre que esta página falar "ver §X",
> é referência ao decisions.md.
>
> Atualize esta página conforme as sprints forem fechando — marque
> checkboxes, mova "estado atual", anote blockers reais.
>
> **Práticas de engenharia (todas as sprints):** ver `decisions.md §20`.
> Resumo: harness engineering (core sem UI, contratos pydantic, filesystem
> as state, providers via interface, config isolada) + TDD red-green-refactor
> por feature. Cada sprint abaixo tem subseção **"Como implementar (TDD)"**
> com testes a escrever antes das tasks.

## Estado atual

**Data:** 2026-05-07
**Sprint ativa:** **Sprint 2 — Roteiro real** (próxima)
**Sprint mais recente fechada:** Sprint 1 — Foundations ✅ (29 testes verdes, `final.mp4` gerado via Fakes em `stories/2026-05-07-raposa-curiosa/`)
**Bloqueios reais:** nenhum. Sprint 0 paraleliza — falta só `gcloud auth application-default login` + `.env` populado pra começar Sprint 2.

---

## Visão geral das sprints

| # | Sprint | Fases do MVP (§13 decisions.md) | Tempo focado | Saída observável |
|---|---|---|---|---|
| 0 | **Pré-flight** | — (operacional, sem código) | 1–2h dispersas | Contas, secrets, configs prontos |
| 1 | **Foundations** | Fase 0 + Fase 1 | 1,5 dia | `contadinhos run stories/test/` produz MP4 fake (sem custo) |
| 2 | **Roteiro real** | Fase 2 | 1–2 dias | `contadinhos script <id>` gera roteiro JSON válido a partir de áudio real, com pré-gate |
| 3 | **Visuais** | Fase 2.5 + Fase 3 | 1,5 dia | Vinhetas estáticas em `assets/` + imagens-chave aprovadas por story |
| 4 | **Vídeo + áudio** | Fase 4 + Fase 5 | 3–5 dias | `final.mp4` completo com narração e música, sem upload |
| 5 | **Publish** | Fase 6 + Fase 7 | 2–3 dias | `contadinhos publish` põe vídeo no canal como `private` |
| 6 | **Telegram** | Fase 7.5 | 2–3 dias | Você manda áudio no iPhone, bot retorna `final.mp4` no chat |
| 7 | **Calibração** | Fase 8 | 4 semanas calendário | 10–20 vídeos rodados, prompts afinados, `publish_mode` decidido |

**Total trabalho focado Sprints 1–6:** ~12–17 dias.
**Calendário realista** (1–2h/dia, projeto pessoal noturno): **4–7 semanas** até Sprint 6 entregue. Sprint 7 (calibração) começa depois.

---

## Sprint 0 — Pré-flight (operacional, sem código)

> Coisas que precisam estar prontas **antes** que o pipeline real (Sprints 4+)
> consiga rodar. Não bloqueiam Sprints 1–3 — você pode ir fazendo enquanto
> codifica.

### Checklist

#### Contas e identidade
- [x] Canal YouTube `@contadinhos` criado
- [x] Verificação SMS do canal (pré-req `thumbnails.set` — ver §8.5)
- [x] Bot `@contadinhosBot` criado no BotFather
- [x] Pasta no Drive: `Backup/contadinhos/` (criada manual ou pelo primeiro `rclone sync`)
- [ ] **2FA forte na conta Google** (app authenticator ou YubiKey) — fazer **antes do primeiro upload pago** (§19 galho de segurança)

#### Google APIs (necessário antes do Sprint 3 para imagens, Sprint 4 para vídeo, Sprint 5 para YouTube)

**Caminho A — Gemini API direto (default Sprint 3+, decidido em 2026-05-07):**
- [x] `GOOGLE_GENERATIVE_AI_API_KEY` no `.env` — atende Veo + Nano Banana + Gemini multimodal (pós-gate). Crédito Google associado à key.

**Caminho B — Vertex AI + ADC (futuro, ver galho §19 de `decisions.md`):**
- [ ] Projeto Google Cloud criado (ex.: `contadinhos-prod`) — só quando migrar pra Vertex
- [ ] Vertex AI API ativada — só no caminho B
- [ ] `gcloud auth application-default login` — só no caminho B
- [ ] `gcloud auth application-default set-quota-project <PROJECT>` — só no caminho B

**YouTube (Sprint 5, independente do caminho A/B):**
- [ ] **YouTube Data API v3** ativada num projeto Google Cloud (qualquer)
- [ ] OAuth desktop client criado em "APIs & Services > Credentials"
- [ ] `client_secret.json` baixado e salvo em `.secrets/` (gitignored)

#### Secrets locais (em `.env`)
- [x] `GOOGLE_GENERATIVE_AI_API_KEY=...` (Veo + Nano Banana + Gemini multimodal + pré/pós-gate)
- [x] `OPENAI_API_KEY=...` (transcrição com `gpt-4o-transcribe` + roteirista com `gpt-5-mini`)
- [ ] `ELEVENLABS_API_KEY=...` (TTS — necessário Sprint 4)
- [ ] `TELEGRAM_BOT_TOKEN=...` (do BotFather — necessário Sprint 6)
- [ ] `KLING_API_KEY=...` (opcional, fallback Veo)
- [ ] `GOOGLE_CLOUD_PROJECT=...` (opcional, só caminho B — Vertex AI)
- ~~`ANTHROPIC_API_KEY`~~ — dropado da stack em 2026-05-07 (roteirista virou OpenAI)

#### Drive + rclone (necessário antes da Sprint 4 idealmente)
- [ ] `brew install rclone`
- [ ] `rclone config` → adicionar remote `drive:` apontando pro Drive da conta Google
- [ ] Teste: `rclone lsd drive:` lista pastas do Drive
- [x] `.rcloneignore` no repo — feito na Sprint 1

### Definition of Done

✅ Todos os checkboxes acima marcados. Nenhum secret faltando. ADC do Google
funcionando (`gcloud auth application-default print-access-token` retorna token).

---

## Sprint 1 — Foundations

> **Fim-a-fim feio antes de polido bonito** (§4). Pipeline tracer-bullet com
> stubs, sem custo de API real, valida o **fluxo** e a estrutura.

### Pré-requisitos
- Sprint 0 parcial: pelo menos `uv` instalado e Python 3.12+ disponível.
- **Não precisa** de Google Cloud nem secrets ainda.

### Tasks

#### Fase 0 — Bootstrap (½ dia)
- [x] `uv init` na raiz do repo
- [x] `pyproject.toml` com deps básicas: `typer`, `pydantic`, `pydantic-settings`, `pyyaml`, `python-dotenv`, `httpx`, `python-slugify`
- [x] `uv venv` cria `.venv/` (gitignored)
- [x] Estrutura de diretórios conforme §12:
  ```
  src/contadinhos/{__init__.py,core/,frontends/}
  src/contadinhos/core/{config.py,story.py,schemas.py,...}
  src/contadinhos/frontends/cli/main.py
  config/{pipeline.yaml,style.yaml,policy.yaml,youtube.yaml,budget.yaml,voices.yaml,providers.yaml,quality_bar.yaml,telegram.yaml,prompts/}
  assets/{intro.mp4,outro.mp4,music/,fonts/,characters/}
  stories/.gitkeep
  .secrets/.gitkeep
  tests/{unit/,integration/}
  scripts/
  ```
- [x] `.gitignore` cobre: `.venv/`, `.secrets/`, `stories/*` (mas não `.gitkeep`), `__pycache__/`, `*.pyc`, `veo3/`, `assets/music/*`, `.bot_state.json`
- [x] `.rcloneignore` na raiz (lista de §14.1)
- [x] CLI esqueleto: `contadinhos --help` lista subcomandos (`new`, `transcribe`, `script`, `images`, `video`, `tts`, `assemble`, `publish`, `run`, `status`)
- [x] `core/config.py` carrega YAMLs (`load_config(name)`) — sem `pydantic-settings` por enquanto, escopo Sprint 1 só precisa de dict
- [x] `core/story.py` define `Story` (path, status, leitura/escrita de roteiro.json) **+ context manager `Story.lock()`** via `fcntl.flock` em `stories/<id>/.lock` (§9.7 de `decisions.md`)
- [x] `core/story.py::Story.create()` resolve colisão de nome com sufixo numérico (§9.8)
- [x] `core/schemas.py` define pydantic models do roteiro JSON e `policy_check` (§3.1, §7.4)
- [x] `core/providers/retry.py` — decorator `@retryable(provider="...")` com política de §8.8 (3 tentativas, exponential backoff 1s/4s/16s, jitter ±25%, só 5xx/timeout/network). Sem providers reais ainda, mas decorator pronto pras Sprints 2+.
- [x] `core/providers/exceptions.py` — `ProviderError(provider, attempt, original)`

#### Fase 1 — Tracer bullet com stubs (1 dia)

Cada subcomando do CLI implementado com **Fakes injetados via `--with-fakes`** (Fakes em `tests/fakes/`, §20.4):

- [x] `contadinhos new <slug>` cria `stories/<YYYY-MM-DD>-<slug>/` com estrutura padrão (sem audio placeholder — usuário copia o real)
- [x] `contadinhos transcribe <story>` chama `Transcriber.transcribe`, escreve `transcript.txt`
- [x] `contadinhos script <story>` chama `Roteirista.generate` + `PreGateAuditor.audit`, escreve `roteiro.json`
- [x] `contadinhos images <story>` chama `ImageGenerator.generate(n=4)` por personagem; primeira candidata como `chosen.png` (Sprint 1; Sprint 3 introduz prompt humano)
- [x] `contadinhos video <story>` gera 1 clip por cena (I2V se `imagem_chave_ref` setada, senão T2V)
- [x] `contadinhos tts <story>` gera 1 narração WAV por cena
- [x] `contadinhos assemble <story>` concat real dos clips via ffmpeg → `final.mp4`
- [x] `contadinhos publish <story>` chama `PostGate.audit` + `YouTubeUploader.upload`, escreve `upload_result.json`
- [x] `contadinhos run <story>` chama `pipeline.run_all` que itera `next_action` até `done`
- [x] `contadinhos status <story>` imprime `next_action` lendo o filesystem

### Como implementar (TDD)

> **Princípio:** core não importa frontend; CLI é só `frontends/cli` chamando funções puras de `core/`. Antes de qualquer task, escrever os testes abaixo (red). Depois implementar até virar verde.

**Testes (escrever primeiro, em ordem):**

1. `tests/unit/test_schemas.py`
   - `test_roteiro_minimo_valida` — pydantic aceita fixture `roteiros/valido_minimo.json`
   - `test_roteiro_sem_cenas_falha` — `ValidationError` em fixture `roteiros/invalido_sem_cenas.json`
   - `test_policy_check_default_ok` — `PolicyCheck()` cospe `verdict="ok"`, flags vazias
2. `tests/unit/test_story_io.py`
   - `test_story_create_estrutura` — `Story.create("test")` cria dir com sub-dirs `images/`, `clips/`, `audio/`
   - `test_story_load_round_trip` — escrever `roteiro.json` + `Story.load()` lê de volta com mesmos campos
   - `test_next_action_inicial` — story só com `audio.m4a` → `next_action == "transcribe"`
   - `test_collision_appendsufixo` — criar `2026-05-07-raposa` 2× → segundo vira `2026-05-07-raposa-2` (§9.8)
   - `test_lock_bloqueia_segundo_processo` — adquirir lock no PID A; PID B (subprocess) tenta e recebe `BlockingIOError` (§9.7)
3. `tests/unit/test_config_loader.py`
   - `test_load_pipeline_yaml_vazio` — YAML vazio carrega defaults sem crash
   - `test_load_yaml_inexistente` — arquivo ausente → erro claro (`FileNotFoundError` com path)
4. `tests/unit/test_retry_decorator.py`
   - `test_retry_em_503_tres_vezes` — função decorada que sempre cospe `httpx.HTTPStatusError(503)` é chamada 3× e levanta `ProviderError`
   - `test_no_retry_em_400` — função que cospe `400` é chamada 1× e levanta na hora (§8.8)
   - `test_no_retry_em_review_required` — função de gate que retorna `verdict="review_required"` **não** dispara retry
5. `tests/integration/test_pipeline_with_fakes.py`
   - `test_run_completo_gera_final_mp4` — `contadinhos run --with-fakes stories/test/` produz `final.mp4` real, custo zero, sem chamadas HTTP

**Implementação (depois dos testes em red):**

Seguir tasks das Fases 0 e 1 acima. Conforme cada teste vira verde, marcar checkbox correspondente. **Fakes ficam em `tests/fakes/`** (§20.4 de `decisions.md`), não em `core/`. CLI ganha flag `--with-fakes` (ou env `CONTADINHOS_FAKES=1`) que injeta os Fakes em vez dos providers reais.

**Contract tests inicializados nesta sprint** (§20.6 a de `decisions.md`):
Criar esqueleto vazio de `tests/contracts/` com classes abstratas pra cada provider (`VideoGeneratorContract`, `TTSProviderContract`, `ImageGeneratorContract`, `RoteiristaContract`, `PreGateAuditorContract`, `PostGateContract`, `YouTubeUploaderContract`). Classes apenas declaram `@pytest.fixture def generator(self): raise NotImplementedError`. Os métodos de teste são preenchidos nas sprints subsequentes conforme cada interface ganha primeira impl Real.

> **Sprint 1 não tem smoke real** porque ainda não existe provider real. O equivalente: `uv run contadinhos run --with-fakes stories/test/` precisa rodar limpo, ledger zerado, `final.mp4` montado pelo ffmpeg real (a partir de placeholders dos Fakes).

**Boas práticas a observar nesta sprint:**
- Pipeline core **não importa** `frontends/` (verificar grep antes do PR).
- `core/schemas.py` é a primeira coisa a escrever — outros módulos dependem.
- `Story.next_action()` é função pura: lê dir, retorna string. Sem cache, sem side effect.
- Configs YAML **nunca** importadas como módulo Python — sempre via `core/config.py::load(name)`.

### Files entregues
- `pyproject.toml`, `uv.lock`
- `src/contadinhos/**` (core + frontend cli, todos com providers reais ou flag `--with-fakes`)
- `config/**` (YAMLs vazios mas válidos por pydantic-settings)
- `tests/fixtures/` (placeholder PNG/MP4/WAV/m4a + `roteiros/*.json`)
- `tests/fakes/` (Fakes de todos os providers — substitui "stubs hardcoded")
- `tests/unit/test_schemas.py`, `tests/unit/test_story_io.py`, `tests/unit/test_config_loader.py`
- `tests/integration/test_pipeline_with_fakes.py`

### Definition of Done

✅ `uv run contadinhos run stories/2026-05-04-test/` roda do início ao fim,
gera `final.mp4` (trash) sem fazer nenhuma chamada HTTP/API. **Custo: US$0.**

✅ `git status` limpo (todos os artefatos relevantes ignorados pelo `.gitignore`).

✅ Estrutura de diretórios espelha §12.

---

## Sprint 2 — Roteiro real

> Primeira chamada de API real. Foco: extrair sinal limpo de áudio bagunçado.
> Pré-gate começa a operar.

### Pré-requisitos
- Sprint 1 ✅
- `OPENAI_API_KEY` no `.env` (cobre **transcrição** com `gpt-4o-transcribe` e **roteirista** com `gpt-5`, §5)
- `GOOGLE_GENERATIVE_AI_API_KEY` no `.env` (pré-gate com `gemini-2.5-flash`, §7.1)
- (Opcional) Áudio de teste real em `tests/fixtures/audio/historia_real.m4a` (uma história sua de 2–3 min, gitignored se sensível)

### Tasks (Fase 2 — 1–2 dias)

- [ ] Substituir stub do `transcribe`: integrar OpenAI **`gpt-4o-transcribe`** (`core/transcribe.py::OpenAITranscriber`); modelo lido de `config/providers.yaml::transcribe.model`
- [ ] Substituir stub do `script`:
  - [ ] Carregar prompt do roteirista de `config/prompts/script.md` — seguir §3.3 (system prompt explícito, 1–2 few-shot, style guide externalizado, constraints negativos)
  - [ ] Chamar OpenAI **`gpt-5-mini`** com structured output (`response_format=json_schema` sobre o pydantic `Roteiro`); modelo lido de `config/providers.yaml::script.model`. Fallback `gpt-5.5` reservado pra Sprint 7 se calibração apontar dor.
  - [ ] Validar saída JSON contra pydantic (`Roteiro` schema)
  - [ ] Adicionar `sinopse_curta` ao schema do roteiro (§8.3) — **já contemplado** no schema entregue na Sprint 1
- [ ] Provider real ganha `@retryable(provider="openai")` (Sprint 1 §8.8 já tem o decorator)
- [ ] Implementar pré-gate como **chamada LLM separada** (§7.1):
  - [ ] `core/policy/pre_gate.py::GeminiPreGateAuditor`: recebe `Roteiro`, retorna `PolicyCheck`
  - [ ] Prompt em `config/prompts/pre_gate.md` (persona de auditor estrito)
  - [ ] Modelo **`gemini-2.5-flash`** via `GOOGLE_GENERATIVE_AI_API_KEY` (config em `config/policy.yaml::pre_gate.model`) — **provider diferente do roteirista** garante independência (§7.1)
  - [ ] Sobrescreve `policy_check` no `roteiro.json`
  - [ ] Custo registrado no ledger (`step: "pre_gate", paid_via: "google_credits"`)
- [ ] Implementar bloqueio do CLI quando `policy_check.verdict == "review_required"`:
  - [ ] CLI mostra flags + abre `$EDITOR` no `roteiro.json`
  - [ ] Após salvar, re-rodar pré-gate só na parte editada (ou validar manualmente)
- [ ] Snapshot de prompts em `prompts_snapshot.json` na story (§16)
- [ ] Cost ledger: registrar custos de transcribe e script com `paid_via` (§11.3)
- [ ] Tests:
  - [ ] `tests/integration/test_script.py` com roteiro mock pra validar schema
  - [ ] `tests/unit/test_pre_gate.py` com casos de hard fail/soft fail

### Como implementar (TDD)

**Testes (escrever primeiro):**

1. `tests/unit/test_pre_gate_logic.py`
   - `test_pre_gate_bloqueia_violencia` — fixture `roteiros/violencia.json` + Fake LLM que devolve flag `violencia` → `verdict == "review_required"`
   - `test_pre_gate_passa_limpo` — fixture `roteiros/valido_completo.json` + Fake LLM benigno → `verdict == "ok"`
   - `test_pre_gate_merge_de_flags` — múltiplas flags são preservadas, não sobrescritas
2. `tests/unit/test_script_schema.py`
   - `test_llm_cospe_json_invalido` — `FakeRoteirista` que devolve JSON sem `cenas` → `ValidationError` no caller
   - `test_sinopse_curta_obrigatoria` — schema rejeita roteiro sem `sinopse_curta` (§8.3)
3. `tests/integration/test_script_e2e_com_fakes.py`
   - `test_script_full_flow` — `audio.m4a` real (fixture pequena) → transcribe Fake → script Fake → pre_gate Fake → `roteiro.json` válido em disco
4. `tests/integration/test_cli_bloqueia_em_review.py`
   - `test_cli_aborta_quando_review_required` — invocar `contadinhos script` com Fake que cospe `review_required` → exit code != 0, mensagem clara

**Implementação:**

Seguir tasks acima. Pré-gate é **chamada LLM separada** (§7.1 de `decisions.md`) — `FakeRoteirista` e `FakePreGateAuditor` são test doubles distintos.

**Boas práticas a observar:**
- Prompt do roteirista vive em `config/prompts/script.md` — **carregado em runtime**, não embutido em string Python.
- `prompts_snapshot.json` é gravado **antes** da chamada LLM (§16.4) — testar que mesmo se a chamada falhar, o snapshot existe.
- Cost ledger ganha duas linhas (`script` + `pre_gate`); testar que ambas têm `paid_via` correto.
- Caso de teste do "áudio violento propositalmente" da DoD vira `tests/integration/test_pre_gate_violence_real.py` **opcional** com `pytest -m real_llm` (skip por padrão; rodar manual antes de fechar sprint).

### Files entregues
- `core/transcribe.py`
- `core/script/{prompts.py,llm.py}`
- `core/policy/pre_gate.py`
- `config/prompts/script.md`
- `config/prompts/pre_gate.md`
- `config/prompts/style.md` (string de estilo aquarela)
- `config/policy.yaml` (modelo do pré-gate, threshold de severity, lista de category)
- `tests/fakes/fake_pre_gate.py`
- `tests/unit/test_pre_gate_logic.py`, `tests/unit/test_script_schema.py`
- `tests/integration/test_script_e2e_com_fakes.py`, `tests/integration/test_cli_bloqueia_em_review.py`

### Definition of Done

✅ `uv run contadinhos script stories/<id>/` recebe `audio.m4a` real, produz
`roteiro.json` que valida no pydantic.

✅ Roteiro contém `sinopse_curta` (1–2 frases) e `policy_check` populado.

✅ Caso de teste: rodar com áudio "violento" propositalmente — pré-gate
levanta flag de `medo`/`violencia`, CLI bloqueia.

✅ `prompts_snapshot.json` tem cópia literal dos prompts usados.

✅ `cost_ledger.json` mostra custo nominal e `paid_via` corretos.

✅ **Smoke real (§20.6 de `decisions.md`):** rodar `uv run contadinhos script stories/smoke-s2-<date>/` com áudio real, **sem `--with-fakes`**. Roteiro real produzido, schema valida, pré-gate roda com LLM real. Se quebrar, atualizar contract test + Fake antes de fechar a sprint.

---

## Sprint 3 — Visuais (vinhetas + imagens-chave)

> Primeiro contato com Nano Banana. Termina com assets prontos pra animar.

### Pré-requisitos
- Sprint 1 ✅
- Sprint 0: `GOOGLE_GENERATIVE_AI_API_KEY` no `.env` (caminho A — default 2026-05-07)
- Sprint 2 **não é** pré-requisito estrito — mas você precisa ter um roteiro real
  pra exercitar o `images` no fim do sprint. Ordem prática: 2 → 3.

### Tasks

#### Fase 2.5 — Assets de marca (½ dia)
- [ ] Definir prompt de identidade visual em `config/prompts/brand.md`
- [ ] Script `scripts/generate_brand_assets.py` (oneshot):
  - [ ] Gera vinheta abertura (Nano Banana → Pillow finaliza texto se preciso)
  - [ ] Gera vinheta fechamento (idem)
  - [ ] Renderiza ambas como MP4 estático via ffmpeg (`-loop 1 -t 2` ou `-t 3`)
  - [ ] Salva em `assets/intro.mp4` e `assets/outro.mp4`
- [ ] Documentar prompt usado em `docs/reference/brand-prompts.md`

> **Opcional:** retrato canônico da Clarinha em `assets/characters/clarinha.png`.
> Por padrão **fora** desta sprint (consistente com Lote 6 = Nano Banana T2I).
> Se a Clarinha "drifar" entre vídeos no Sprint 7, voltar aqui.

#### Fase 3 — Imagens-chave (1 dia)
- [ ] `core/images/base.py` define `ImageGenerator` interface
- [ ] `core/images/nano_banana.py` implementa via `google-genai` (Vertex AI)
- [ ] CLI `contadinhos images <story>`:
  - [ ] Para cada `imagem_chave` no roteiro: gerar 4 candidatas
  - [ ] `open` no macOS abre as 4 no Preview
  - [ ] CLI pede índice da escolhida (typer prompt)
  - [ ] Copia escolhida pra `images/<personagem>/chosen.png`
- [ ] Snapshot de prompts dos personagens (§16)
- [ ] Cost ledger atualizado
- [ ] Tests: `tests/integration/test_images.py` (com mock do provider)

### Como implementar (TDD)

**Testes (escrever primeiro):**

1. `tests/unit/test_image_generator_interface.py`
   - `test_fake_implementa_contrato` — `FakeImageGenerator(NanoBananaGenerator interface).generate(prompt, n=4)` retorna 4 paths PNG válidos
   - `test_real_e_fake_compartilham_assinatura` — `inspect.signature` de `NanoBananaGenerator.generate` == `FakeImageGenerator.generate`
2. `tests/unit/test_image_choice_persists.py`
   - `test_chosen_png_e_copia` — escolher candidata 2 → `images/raposa/chosen.png` é cópia byte-a-byte de `candidate_2.png`
   - `test_rerun_nao_sobrescreve_chosen` — invocar `images` 2× sem flag `--force` → segunda chamada é no-op
3. `tests/integration/test_brand_assets_idempotente.py`
   - `test_intro_outro_existem_apos_script` — `scripts/generate_brand_assets.py` produz `assets/intro.mp4` e `assets/outro.mp4` que abrem com ffprobe
4. `tests/integration/test_images_e2e_com_fake.py`
   - `test_images_grid_persistido` — pipeline com `FakeImageGenerator` cria `candidate_0..3.png` e `chosen.png` quando seleção é simulada via env var `FAKE_IMAGE_CHOICE=2`

**Implementação:**

Tasks acima. `core/images/base.py::ImageGenerator` define o contrato; `nano_banana.py` é só uma impl. Geração de vinhetas (`scripts/generate_brand_assets.py`) **não usa pipeline core** — é one-shot puro chamando Nano Banana direto.

**Boas práticas a observar:**
- `chosen.png` é **cópia, não symlink** (§13 Fase 3 de `decisions.md`) — testar com `os.path.realpath`.
- Prompt da imagem-chave entra no `prompts_snapshot.json` da story (§16.2).
- Custo Nano Banana com `paid_via=google_credits`; testar que o ledger marca correto.
- `scripts/generate_brand_assets.py` deve ser idempotente: rodar 2× sem mudar config = mesmo arquivo. Se prompt mudou em `brand.md`, regerar (decidir critério: hash do prompt no nome?).

### Files entregues
- `core/images/{base.py,nano_banana.py}`
- `assets/intro.mp4`, `assets/outro.mp4`
- `config/prompts/brand.md`
- `docs/reference/brand-prompts.md`
- `scripts/generate_brand_assets.py`
- `tests/fakes/fake_image_generator.py`
- `tests/unit/test_image_generator_interface.py`, `tests/unit/test_image_choice_persists.py`
- `tests/integration/test_brand_assets_idempotente.py`, `tests/integration/test_images_e2e_com_fake.py`

### Definition of Done

✅ `assets/intro.mp4` e `assets/outro.mp4` existem, abrem no QuickTime, soam/parecem corretos.

✅ `uv run contadinhos images stories/<id>/` para um roteiro real gera 4 candidatas
por personagem e grava as escolhas em `images/<personagem>/chosen.png`.

✅ Cost ledger registrou custo nominal Nano Banana com `paid_via=google_credits`.

✅ **Smoke real (§20.6 de `decisions.md`):** `uv run contadinhos images stories/smoke-s3-<date>/` chama Nano Banana real, gera 4 candidatas reais, persiste `chosen.png`. Comparar candidatas reais com `placeholder.png` do Fake — se Real expõe campo/erro que Fake ignora, ajustar contract test + Fake.

---

## Sprint 4 — Vídeo + áudio (porte do `veo3/` + montagem)

> Sprint mais densa. Termina com `final.mp4` completo com narração e música.

### Pré-requisitos
- Sprint 3 ✅ (precisa de imagens-chave aprovadas pra alimentar I2V)
- Sprint 0: `GOOGLE_GENERATIVE_AI_API_KEY` (Veo) + `ELEVENLABS_API_KEY` no `.env`
- `ffmpeg` instalado (`brew install ffmpeg`)
- (Opcional) 5–10 faixas curadas da YT Audio Library em `assets/music/` (em ogg/m4a)

### Tasks

#### Fase 4 — Geração de vídeo (2–3 dias)
- [ ] `core/video/base.py` define `VideoGenerator` interface (`generate_clip(prompt, duration_s, first_frame=None) -> Path`)
- [ ] `core/video/veo.py` — **porte de `veo3/generate.py`**:
  - [ ] Reaproveitar: padrão `genai.Client(vertexai=True)` + `models.generate_videos` + polling 600s
  - [ ] Reaproveitar: `extract_last_frame` via ffmpeg
  - [ ] Reaproveitar: `negative_prompt` (mover pra `config/providers.yaml`)
  - [ ] Adaptar: cenas curtas (8s × ~10) em vez de 3 longas
  - [ ] Modo I2V quando `cena.imagem_chave_ref` setada (`image=Image.from_file(chosen.png)`)
  - [ ] Modo T2V quando não (paisagem pura)
  - [ ] **Sem chaining de last-frame por padrão** (§3.2). Cada cena é independente. Flag `video.chain_first_frame` em `config/pipeline.yaml` fica opt-in experimental, desabilitado por padrão.
- [ ] `core/video/kling.py` — implementação alternativa (provider plugável, mas pode ser stub agora)
- [ ] `core/video/factory.py` lê `config/providers.yaml` `video.provider` e instancia o correto
- [ ] **Pre-flight check** (§11.2): antes de chamar Veo, somar estimativa nominal (`len(cenas) × duracao_média × cost_per_second` lido de `config/providers.yaml`) e abortar se passar do teto, **antes de gastar**
- [ ] Hard-fail post-hoc no teto por-vídeo (US$80 nominal Veo na calibração, §11.2 — fallback caso pre-flight tenha subestimado)
- [ ] Cost ledger atualizado com custo nominal Veo
- [ ] Após pipeline funcionar: **deletar `veo3/`** ou mover pra `docs/reference/veo3-original.py`

#### Fase 5 — TTS + montagem (1–2 dias)
- [ ] `core/tts/base.py` define `TTSProvider` interface
- [ ] `core/tts/elevenlabs.py` implementa
- [ ] CLI `contadinhos tts <story>`:
  - [ ] Para cada cena no roteiro, gerar narração WAV em `audio/narration_<idx>.wav`
  - [ ] Voice ID padrão em `config/voices.yaml`
- [ ] `core/assemble/ffmpeg.py`:
  - [ ] Concat dos clipes na ordem das cenas
  - [ ] Mix narração por cena com timing correto (offset = soma das durações anteriores)
  - [ ] Música de fundo (rotação de `assets/music/`) com `volume=0.15`
  - [ ] `drawtext` da narração (legendas) por cena
  - [ ] Prepend `assets/intro.mp4`, append `assets/outro.mp4`
  - [ ] Output: `final.mp4` 1080p H.264/AAC 30fps
- [ ] Cost ledger ElevenLabs

### Como implementar (TDD)

**Testes (escrever primeiro):**

1. `tests/unit/test_pre_flight_cost.py`
   - `test_pre_flight_passa_dentro_do_teto` — 10 cenas × 8s × $0.50/s = $40; teto $80 → não aborta
   - `test_pre_flight_aborta_acima_do_teto` — 30 cenas × 10s × $0.50/s = $150; teto $80 → `BudgetExceededError`
   - `test_pre_flight_le_custo_de_config` — `config/providers.yaml::costs_per_second.veo` = 0.50; mudar pra 1.0 → estimativa dobra
2. `tests/unit/test_video_generator_contract.py`
   - `test_i2v_aceita_first_frame` — `FakeVideoGenerator.generate(prompt, first_frame=path)` produz MP4
   - `test_t2v_sem_first_frame` — `generate(prompt)` sem `first_frame` produz MP4
   - `test_chain_default_off` — `config/pipeline.yaml::video.chain_first_frame` ausente → `False` (§3.2 de `decisions.md`)
3. `tests/unit/test_assemble_concat_order.py`
   - `test_concat_segue_idx_das_cenas` — clipes `scene_03.mp4`, `scene_01.mp4`, `scene_02.mp4` no disco → final.mp4 com ordem 1, 2, 3 (não ordem do filesystem)
   - `test_assemble_inclui_intro_outro` — final.mp4 começa com intro.mp4, termina com outro.mp4
4. `tests/integration/test_assemble_ffmpeg_real.py`
   - `test_audio_sync_offset_correto` — narração da cena 2 começa em `t = duracao_cena_1`. Verificado lendo timestamps via ffprobe.
   - `test_output_1080p_h264_aac` — `final.mp4` tem stream de vídeo 1920×1080 H.264 e áudio AAC

**Implementação:**

Porte de `veo3/generate.py` segue ordem: contrato (`base.py`) → impl Veo (`veo.py`) → factory (`factory.py`) → impl Kling como stub. Pre-flight check (§11.2 de `decisions.md`) é módulo separado em `core/budget.py::pre_flight(roteiro, provider)` chamado **antes** de qualquer chamada Veo.

**Boas práticas a observar:**
- **Sem chaining de last-frame por padrão** (§3.2). Não copiar essa parte de `veo3/`.
- **Pre-flight aborta antes de gastar** (§11.2). Testar que se o estimado passa do teto, **nenhuma chamada HTTP** é feita.
- Negative prompt sai de `config/providers.yaml`, não hardcoded.
- Custo nominal **sempre** registrado no ledger, mesmo em crédito Google.
- Teste de integração ffmpeg roda em CI sem rede; testes Veo/Kling reais ficam atrás de marker `pytest -m real_provider` (skip por padrão).

### Files entregues
- `core/video/{base.py,veo.py,kling.py,factory.py}`
- `core/tts/{base.py,elevenlabs.py}`
- `core/assemble/ffmpeg.py`
- `core/budget.py` (pre-flight estimator)
- `config/voices.yaml`, `config/providers.yaml` populados (incl. `costs_per_second`)
- `tests/fakes/fake_video_generator.py`, `tests/fakes/fake_tts.py`
- `tests/unit/test_pre_flight_cost.py`, `tests/unit/test_video_generator_contract.py`, `tests/unit/test_assemble_concat_order.py`
- `tests/integration/test_assemble_ffmpeg_real.py`

### Definition of Done

✅ `uv run contadinhos run stories/<id>/` (sem `publish`) produz `final.mp4`
1080p com narração, música, vinhetas, legendas. Reproduzível em QuickTime.

✅ Custo nominal do vídeo registrado, abaixo do teto US$60.

✅ `prompts_snapshot.json` tem prompts de imagens-chave + negative prompt Veo.

✅ Pasta `veo3/` deletada ou arquivada em `docs/reference/`.

✅ Você assistiu o vídeo inteiro e o estilo aquarela tá decente.

✅ **Smoke real (§20.6 de `decisions.md`):** `uv run contadinhos run stories/smoke-s4-<date>/` ponta-a-ponta **sem `--with-fakes`** chama Veo + ElevenLabs reais. Pre-flight check dispara antes de gastar (testar no smoke com roteiro propositalmente caro pra ver abortar). Custo real registrado no ledger. Se Real cospe formato diferente do Fake (codec, duração, metadata), atualizar contract test antes de fechar.

---

## Sprint 5 — Publish (pós-gate + upload)

> Vídeo chega no canal. Como `private` por enquanto (ver §8.2/§8.6).

### Pré-requisitos
- Sprint 4 ✅
- Sprint 0: OAuth desktop client + `client_secret.json` em `.secrets/`
- Sprint 0: `GOOGLE_GENERATIVE_AI_API_KEY` (Gemini multimodal pós-gate)

### Tasks

#### Fase 6 — Pós-gate multimodal (1 dia)
- [ ] `core/policy/post_gate.py`:
  - [ ] Extrai N frame samples do `final.mp4` via ffmpeg (a cada ~7s)
  - [ ] Extrai trecho de áudio (primeiros 30s)
  - [ ] Chama Gemini 2.5 Flash com prompt em `config/prompts/post_gate.md`
  - [ ] Atualiza `policy_check` no `roteiro.json` (mescla flags com pré-gate, §7.4)
- [ ] CLI `contadinhos publish <story>`:
  - [ ] Roda pós-gate
  - [ ] Se `verdict == "review_required"`, bloqueia, mostra flags
  - [ ] Se ok, segue pra upload

#### Fase 7 — Upload YouTube (1–2 dias)
- [ ] `core/upload/auth.py`: OAuth desktop flow, gera/refresh token em `.secrets/youtube_token.json`
- [ ] `core/upload/youtube.py`:
  - [ ] `videos.insert` com:
    - `status.privacyStatus` = lê de `config/youtube.yaml::publish_mode` (private_only / unlisted_review / direct_public; ver §8.2)
    - `status.selfDeclaredMadeForKids = true`
    - `snippet.categoryId = 1`
    - `snippet.defaultLanguage = pt-BR`
    - `snippet.title` via template (sufixo `| contadinhos` lowercase)
    - `snippet.description` via template + `sinopse_curta` (§8.3)
    - `snippet.tags` = lista fixa em config + 1–2 do roteiro
  - [ ] `thumbnails.set` com `images/<protagonista>/chosen.png` redimensionada via Pillow (1280×720, ≤2MB)
  - [ ] Fallback se `thumbnails.set` falhar (canal não verificado): segue sem thumbnail custom
  - [ ] Grava `upload_result.json` com `videoId`, URL, status
- [ ] **Em paralelo:** submeter [auditoria de compliance](https://support.google.com/youtube/contact/yt_api_form) ao Google
- [ ] Quality bar checklist no CLI (§15) antes do botão de promover (mas só relevante quando `publish_mode != private_only`)

### Como implementar (TDD)

**Testes (escrever primeiro):**

1. `tests/unit/test_post_gate_logic.py`
   - `test_post_gate_flagueia_glitch_visual` — Fake multimodal que devolve flag `glitch_visual` → `verdict == "review_required"`
   - `test_post_gate_merge_com_pre_gate` — flags do pré-gate + flags do pós-gate convivem (não sobrescreve, §7.4)
2. `tests/unit/test_youtube_metadata_template.py`
   - `test_titulo_aplica_sufixo_lowercase` — roteiro `titulo="A Raposa Curiosa"` → upload com `"A Raposa Curiosa | contadinhos"`
   - `test_descricao_inclui_sinopse_e_boilerplate` — descrição final tem `sinopse_curta` + `boilerplate_canal` em ordem (§8.3)
   - `test_made_for_kids_sempre_true` — payload de `videos.insert` tem `selfDeclaredMadeForKids: true` (§8.4) — sem flag pra desligar
3. `tests/unit/test_publish_bloqueia_em_review.py`
   - `test_publish_aborta_em_review_required` — pós-gate cospe `review_required` → `FakeYouTubeUploader.upload` **não** é chamado
4. `tests/integration/test_publish_e2e_com_fakes.py`
   - `test_publish_grava_upload_result` — pipeline completo com fakes → `upload_result.json` com `videoId`, URL, `status="private"` (default antes de auditoria)

**Implementação:**

`core/policy/post_gate.py` extrai N frames + áudio via ffmpeg, manda pra Gemini multimodal. `core/upload/youtube.py` é wrapper fino sobre `googleapiclient.discovery`. Auth flow em `core/upload/auth.py` separado pra testabilidade (mock `Credentials` no teste).

**Boas práticas a observar:**
- Template do título/descrição vive em `config/youtube.yaml` (§8.3). Nunca f-string em código.
- `publish_mode` lê de config — testar que mudar config muda comportamento sem mexer em código.
- Fallback de `thumbnails.set` (canal não verificado) é **silencioso com log**, não fatal (§8.5).
- Cassette do `videos.insert` real: opcional, só se sentir necessidade — auth desktop flow torna isso chato.

### Files entregues
- `core/policy/post_gate.py`
- `core/upload/{auth.py,youtube.py}`
- `config/prompts/post_gate.md`
- `config/youtube.yaml` populado
- `tests/fakes/fake_post_gate.py`, `tests/fakes/fake_youtube_uploader.py`
- `tests/unit/test_post_gate_logic.py`, `tests/unit/test_youtube_metadata_template.py`, `tests/unit/test_publish_bloqueia_em_review.py`
- `tests/integration/test_publish_e2e_com_fakes.py`

### Definition of Done

✅ `uv run contadinhos publish stories/<id>/` sobe vídeo no canal (como `private`
por enquanto — projeto API ainda não auditado).

✅ Você abre YouTube Studio e vê o vídeo lá com título correto, descrição,
tags, thumbnail (se canal estiver verificado), made-for-kids ativo.

✅ Pós-gate bloqueou pelo menos uma vez em vídeo de teste com glitch
proposital.

✅ Auditoria de compliance submetida.

✅ **Smoke real (§20.6 de `decisions.md`):** `uv run contadinhos publish stories/smoke-s5-<date>/` chama Gemini multimodal real + YouTube API real (upload como `private`). Pós-gate flagueia ou aprova com modelo real (não Fake). Resposta de `videos.insert` real validada — atualizar contract do `YouTubeUploader` se schema vier diferente do Fake.

---

## Sprint 6 — Telegram

> Frontend de operação. Você manda áudio do iPhone, recebe vídeo no chat.

### Pré-requisitos
- Sprint 5 ✅ (pipeline completo funcionando via CLI)
- Sprint 0: `TELEGRAM_BOT_TOKEN` no `.env`

### Tasks (Fase 7.5 — 2–3 dias)

- [ ] `pyproject.toml`: adicionar `python-telegram-bot >= 21.7`
- [ ] `frontends/telegram/bot.py` — entrypoint async, polling
- [ ] `frontends/telegram/handlers.py`:
  - [ ] Handler de áudio: cria story, dispara `transcribe + script` em background task
  - [ ] Handler de callback button (inline keyboard responses)
  - [ ] Handler de comando `/cancel` e `/status`
- [ ] `frontends/telegram/keyboards.py`:
  - [ ] Roteiro review: ✅ aprovar / ✏️ pedir nova versão / ❌ abandonar
  - [ ] Imagens: media group de 4 + buttons `1`/`2`/`3`/`4`/`🔄 regerar` por personagem
  - [ ] Pós-gate: 🚀 subir / ❌ abandonar / 🎬 regerar cena (com submenu)
  - [ ] Quality bar: 10 toggles (§15) + botão "🚀 promover"
- [ ] `frontends/telegram/flow.py`: state machine que mapeia `next_action` da story → próxima mensagem
- [ ] `frontends/telegram/auth.py`: allowlist de `chat_id` lida de `config/telegram.yaml`
- [ ] Idempotência via `.bot_state.json` com `last_processed_update_id` (§17.2)
- [ ] Crash recovery: ao subir, se `current_story_id` setado, manda mensagem de decisão (§17.3)
- [ ] `scripts/com.contadinhos.bot.plist` — launchctl plist com `caffeinate -dims` (§17.1)
- [ ] `scripts/install_launchctl.sh` — copia plist pro `~/Library/LaunchAgents/` e `launchctl load`
- [ ] CLI continua funcionando em paralelo (sanity check)

### Como implementar (TDD)

**Testes (escrever primeiro):**

1. `tests/unit/test_telegram_allowlist.py`
   - `test_chat_id_fora_da_allowlist_ignorado` — handler recebe update de `chat_id` desconhecido → não chama core, loga warning
   - `test_chat_id_permitido_processa` — `chat_id` em `config/telegram.yaml::allowlist` → handler segue
2. `tests/unit/test_idempotencia_update_id.py`
   - `test_update_ja_processado_skip` — `.bot_state.json::last_processed_update_id = 100`, update com `update_id=100` chega → skip
   - `test_update_novo_atualiza_state` — update com `update_id=101` → processa e grava `101`
   - `test_write_atomico` — simular crash entre write e rename → state file íntegro (não corrompido)
3. `tests/unit/test_state_machine_flow.py`
   - `test_next_action_mapeia_para_mensagem` — `Story.next_action() == "review_script"` → `flow.next_message(story)` retorna mensagem com inline keyboard de aprovação
   - `test_next_action_mapeia_para_imagens` — `next_action == "review_images"` → media group de 4 + buttons
4. `tests/unit/test_crash_recovery.py`
   - `test_bot_subindo_com_story_em_curso_pergunta` — `.bot_state.json::current_story_id != null` no startup → handler manda mensagem de decisão (§17.3)
5. `tests/integration/test_single_story_queue.py`
   - `test_audio_durante_processamento_entra_na_fila` — simular 2 áudios em 1s; segundo recebe resposta de fila

**Implementação:**

Usa `python-telegram-bot` async. State machine em `flow.py` é função pura sobre `Story` — fácil de testar. Handlers chamam core via funções, **nunca** importam `cli/`. `auth.py` carrega allowlist de YAML.

**Boas práticas a observar:**
- Bot **não duplica lógica do core** — só traduz updates → chamadas de core e core → mensagens.
- `flow.next_message()` é função pura, testada sem mock do Telegram.
- `.bot_state.json` é write-then-rename atômico (testar com kill simulado).
- `caffeinate -dims` no plist é detalhe de operação, não testado em unidade. Smoke test manual: `launchctl load && load` 5×, bot sobe sempre.
- Crash recovery aciona prompt humano (§17.3); auto-resume é proibido por princípio.

### Files entregues
- `frontends/telegram/**`
- `scripts/com.contadinhos.bot.plist`
- `scripts/install_launchctl.sh`
- `config/telegram.yaml`
- `tests/unit/test_telegram_allowlist.py`, `tests/unit/test_idempotencia_update_id.py`, `tests/unit/test_state_machine_flow.py`, `tests/unit/test_crash_recovery.py`
- `tests/integration/test_single_story_queue.py`

### Definition of Done

✅ Você manda áudio (voice message) pro `@contadinhosBot`. Bot cria story,
processa, retorna `final.mp4` no chat.

✅ Bot sobrevive a `launchctl unload && load` sem reprocessar updates antigos.

✅ Mac dorme tela mas bot continua respondendo (caffeinate).

✅ Crash mid-pipeline → ao reiniciar, bot pergunta no chat o que fazer.

✅ **Smoke real (§20.6 de `decisions.md`):** mandar áudio real do iPhone pro `@contadinhosBot` rodando via launchctl. Pipeline completo executa com providers reais. Bot devolve `final.mp4` no chat. Se UX divergir do que os testes unit/integration cobriram (timing de resposta, comportamento do callback), corrigir e adicionar caso ao corpus de regressão.

---

## Sprint 7 — Calibração

> Operação real, sem código novo necessariamente. Coleta-se dados pra
> ajustar prompts e decidir migração de regime.

### Pré-requisitos
- Sprints 1–6 ✅ (pipeline e bot funcionando ponta-a-ponta)
- Auditoria de compliance aprovada (idealmente — senão vídeos ficam `private`)

### Tasks (Fase 8 — 4 semanas calendário)

#### Loop semanal
- [ ] Conta uma história, grava, manda pro bot
- [ ] Faz a curadoria pelos botões do Telegram
- [ ] Promove ou abandona conforme `quality_bar` (§15)
- [ ] Anota observações em `docs/calibration-log.md`

#### Após ~10 vídeos
- [ ] Cruzar `quality_review.hard_fails` × `policy_check` do pós-gate
- [ ] Se pós-gate deixou passar hard fail múltiplas vezes: ajustar prompt em `config/prompts/post_gate.md`
- [ ] Se pré-gate disparou false positives: ajustar `config/prompts/script.md`
- [ ] Anotar tendências de `soft_fails` mais comuns: pode revelar problema sistêmico (música alta? aquarela fraca?)

#### Após ~20 vídeos
- [ ] Decidir: migrar `publish_mode` → `direct_public`?
- [ ] Decidir: aumentar cadência (3+/sem)?
- [ ] Decidir: criar retrato canônico da Clarinha (se drift visível)?
- [ ] Decidir: migrar bot pra VPS?

### Como implementar (TDD)

Sprint operacional, **sem código novo necessariamente**. Mas qualquer ajuste de prompt em `config/prompts/*.md` deve ser acompanhado de:

1. **Adicionar caso ao corpus de regressão** em `tests/fixtures/roteiros/` antes de mexer no prompt. Ex.: se vídeo 7 teve hard fail "vibe sombria não pega", criar `roteiros/vibe_sombria_video_7.json` com fixture do roteiro do problema.
2. **Teste novo:** `tests/integration/test_post_gate_regressoes.py::test_video_7_seria_pego_agora` — usa `pytest -m real_llm` com prompt **novo** e asserta `verdict == "review_required"`.
3. **Sem alterar prompt antes do teste falhar** com prompt antigo (red).
4. **Após ajustar prompt, todos os casos da pasta passam** (green). Caso de regressão pego → garantia que ajustes futuros não voltam pra trás.

**Boas práticas a observar:**
- `docs/calibration-log.md` ganha 1 entrada por vídeo (manual). Formato livre mas inclui: data, story_id, hard fails observados, soft fails, decisão (promover / abandonar / regenerar), observação de tendência se aplicável.
- Mudança de modelo do pós-gate (Gemini → Claude → GPT-4o) = mexer 1 linha em `config/policy.yaml`. Suite de testes de regressão deve passar **antes** do swap.
- Decisões tomadas viram entradas em `decisions.md §19` (galhos resolvidos) ou novo §, não só anotação solta.

### Definition of Done (sprint contínua)

Não tem DoD final — Sprint 7 é o regime permanente. "Pronto pra entrar em
modo regime" significa:

✅ Pós-gate calibrado: < 1 falso-positivo a cada 5 vídeos.

✅ Pelo menos 1 ajuste de prompt feito com base em `quality_review` histórico.

✅ Decisões tomadas sobre os 4 pontos acima (registradas em `decisions.md`
abrindo galhos novos se necessário).

---

## Galhos pra abrir DURANTE as sprints (não esquecer)

Estes não são pré-requisitos, são **pontos pra prestar atenção** durante a
execução:

- **Sprint 2:** se LLM roteirista vier com formato JSON inconsistente, abrir galho de "structured output" (response_format=json_schema).
- **Sprint 3:** se Nano Banana der erro de quota mesmo com créditos, checar se a região (`us-central1`?) está correta.
- **Sprint 4:** **monitorar custo Veo** — primeiro vídeo real é teste de fogo da estimativa US$30–55. Se vier muito acima, reabrir §11.4 (talvez Kling antecipado).
- **Sprint 4:** chaining de last-frame fica **desabilitado por padrão** (§3.2). Se o salto visual entre cenas atrapalhar fluxo, considerar habilitar via `config/pipeline.yaml::video.chain_first_frame: true` ou desenhar variante seletiva (chain dentro de mesma sequência narrativa).
- **Sprint 5:** auditoria do Google pode demorar dias-semanas. Mantenha `publish_mode = private_only` até aprovar.
- **Sprint 6:** se Mac dormindo virar dor real antes do esperado, antecipar migração pra VPS (§19).
- **Sprint 7:** se o ritmo "2/sem" se mostrar pesado demais, **reduzir** sem culpa. Anonimato + zero pressão de métrica = você decide o ritmo.

---

## Pontos de re-decisão obrigatórios

Marcar no calendário:

- **Após Sprint 5 (primeiro vídeo `private` no canal):** revisar custo Veo realizado vs. estimado (§11.4).
- **Após Sprint 6 (bot funcionando):** decidir 2FA hardware vs app authenticator (§19).
- **Após 5 vídeos da Sprint 7:** decidir sobre retrato canônico da Clarinha (§19).
- **Após 20 vídeos da Sprint 7:** decidir sobre `publish_mode` (§19).
- **Após 5–10 vídeos reais (Sprint 4–7):** abaixar teto por-vídeo Veo/Kling pra valor calibrado nos dados reais (§19, §11.2).
- **Quando crédito Veo esgotar:** decidir migrar pra Kling (§5, §11.4).
- **Quando Drive free tier (15GB) ficar apertado:** decidir backup retention adicional (§14).
