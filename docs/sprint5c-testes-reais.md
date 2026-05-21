# Sprint 5c — Resolver Vertex AI + executar primeiro teste real

> Continuação direta da [Sprint 5b](./sprint5b-testavel-e2e.md). Sprint 5b
> Fase A entregue (TTS sem ElevenLabs + Veo Lite, commit `fdb62b7`); Fases
> C–E ficaram pendentes — operacionais, sem código novo. Esta sprint
> retoma o caminho até `done` adicionando uma **Fase 0** pra resolver
> primeiro o refator Auth Google → Vertex AI que está em flight no working
> tree de Kaique (não commitado em 2026-05-21).
>
> Por que Sprint 5c e não simplesmente "continuação 5b": Vertex muda
> `deps.py` e `providers.yaml`, conflitando com o que Sprint 5b já
> commitou. Resolver antes do gate barato evita rodar `pytest -m
> real_provider` com auth instável.
>
> **Por quê** das decisões: memória `project_google_auth` (Vertex em flight)
> e `project_testavel_e2e` (Sprint 5b grelha de 2026-05-17). Princípios
> em `decisions.md §20`.

## Pré-requisitos

- Sprint 5b Fase A ✅ (TTS OpenAI/Gemini + Veo Lite no main, suíte 116 verde)
- Working tree limpo em `main` (HEAD = `748dc7e` na hora desta doc) +
  **stash `vertex-code-wip`** preservado (refator Auth Google em flight).
- Keys **em mãos**: `OPENAI_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`.
- Google Cloud: Vertex AI API habilitada no projeto `ai-production-432511`
  (us-central1). YouTube Data API v3 e Generative Language API: já enabled
  (Sprint 5b confirmou).
- `~/.contadinhos/client_secret.json` presente; **token ainda não** cunhado.
- `ffmpeg`/`ffprobe` instalados ✅.
- `gcloud` CLI instalado localmente.

## Tasks

### Fase 0 — Resolver Vertex AI (código + decisão de design)

> Decisão pendente da sessão de auditoria 2026-05-21: Kaique disse "queria
> uma interface para usar Vertex OU Google Gemini API, mas por enquanto e
> Vertex de fato". O stash hoje força Vertex (helper rejeita
> `auth_mode != "vertexai"`). Esta fase cravra o desenho final.

#### F0.1 — Decidir design do toggle `auth_mode`

- [ ] Decidir entre:
  - **A) Toggle plugável** (recomendado): `core/google/client.py` aceita
    `auth_mode: vertexai` (default) **ou** `api_key` lendo `api_key_env`.
    Reabilita rapidamente Gemini API direta se Vertex der problema (quota,
    crédito, region down).
  - **B) Hard switch Vertex**: como o stash está hoje (rejeita `api_key`).
    Menos código, mas perde fallback de emergência.
- [ ] Anotar a escolha em `decisions.md §5` ("Auth Google") com **why**
  curto. Atualizar memória `project_google_auth` no mesmo passo.

#### F0.2 — Aplicar stash + resolver conflitos com Sprint 5b

- [ ] `git stash pop stash@{0}` (recupera os 12 arquivos do refator).
- [ ] Resolver conflitos esperados (Sprint 5b mexeu nos mesmos arquivos):
  - `src/contadinhos/frontends/cli/deps.py` — combinar:
    - Sprint 5b: key TTS **condicional** ao `tts.provider` selecionado.
    - Vertex stash: remoção do `_require_env("GOOGLE_GENERATIVE_AI_API_KEY")`
      (não precisa de env Google se ADC tá ativo).
    - Resultado esperado: `_real_deps()` exige só keys do(s) provider(s)
      ativo(s) **excluindo** Google (que vai por ADC).
  - `tests/unit/test_real_deps_wiring.py` — atualizar pra refletir ambos.
  - `config/providers.yaml` — `auth_mode: vertexai` + `project` + `location`
    + comentário de tier Veo Lite/Fast (Sprint 5b). Já mergeou clean no
    pop anterior; se conflitar de novo, manter os dois blocos.
- [ ] Se F0.1 escolher (A) toggle: editar `core/google/client.py` pra
  aceitar o branch `api_key` (lê `api_key_env` do config, instancia
  `genai.Client(api_key=...)`).
- [ ] Decidir se `auth_mode: vertexai` vai como **default no main**.
  - Se sim: `providers.yaml` commita com `vertexai`.
  - Se não (manter `api_key` como default por enquanto, Vertex opt-in):
    inverter o YAML antes do commit.

#### F0.3 — Suíte verde + smoke contract

- [ ] `uv run pytest -m "not real_provider"` verde.
- [ ] Confirmar que `core/policy/post_gate.py` funciona via `Part.from_bytes`
  (Vertex AI não tem Files API). Limite hard-coded 18 MB cobre vídeos de
  60–90s @ 1080p; documentar como assertion.
- [ ] **Smoke real** (~$0.01–0.05): `uv run pytest -m real_provider
  tests/integration/test_real_providers.py -k "vertex or google" -q`.
  Se contract `PreGate`/`PostGate` divergir do Fake (formato de erro do
  Vertex vs Gemini API direta), atualizar **contract** (não só o caso
  concreto).

#### F0.4 — Commit + push do refator Vertex

- [ ] Commit dedicado: `Sprint 5c Fase 0 — Auth Google: Vertex AI (...)`.
- [ ] Atualizar docs de uma vez (uma passada conexa em vez de doc → código
  → doc → código):
  - `decisions.md §5` Auth Google row (estado final pós-decisão F0.1)
  - `decisions.md §7.2` Pós-gate (inline bytes + limite 18 MB se Vertex)
  - `decisions.md §11.5` (reuso veo3/)
  - `decisions.md §19` — fechar galho "Migrar Gemini API → Vertex" + abrir
    "GCS path no pós-gate" + (se A) "expor toggle implementado, default X"
  - `sprints.md` Sprint 0 Caminho A/B + secrets locais (ajustar pra realidade)
  - `sprint5-setup.md §1` (projeto Vertex em vez de API key)
  - `.env.example` (refletir o que ficou obrigatório vs opcional)
  - `CONTEXT.md` Pós-gate (frame samples → MP4 inline)
  - `CLAUDE.md` seção Auth Google
  - Memória `project_google_auth.md`

### Fase 1 — Setup operacional externo

> Equivalente à Fase C de Sprint 5b. Sem código. Pré-condição pra rodar
> qualquer provider real. Veja [`sprint5-setup.md`](./sprint5-setup.md)
> pros passos completos de OAuth.

- [ ] **2FA forte na conta Google** (`decisions.md §19` galho de segurança)
  — antes do primeiro upload pago. App authenticator (gratuito, 5 min) ou
  YubiKey (~US$50). Decisão: aceitável ainda iniciar testes só com 2FA via
  authenticator app.
- [ ] **OAuth consent screen** configurado: User Type **External**, test
  user `plataformaencantrip@gmail.com` (cf. `sprint5-setup.md §2`).
  Scopes: `youtube.upload`, `youtube.readonly`.
- [ ] **Token YouTube cunhado**: `uv run contadinhos auth-youtube` →
  browser abre, login `plataformaencantrip@gmail.com`, aprovar scopes →
  `~/.contadinhos/youtube_token.json` criado.
  - Confirmar o path real lido por `core/upload/auth.py::token_path()`
    (é fonte de verdade; reconciliar doc se divergir).
- [ ] **`.env` populado** a partir de `.env.example`:
  - `OPENAI_API_KEY=...` (obrigatória)
  - `GOOGLE_GENERATIVE_AI_API_KEY=...` — depende de F0.1: obrigatória se
    toggle ficar em `api_key` por default, **opcional** se ficar em
    `vertexai` (ADC cobre tudo Google).
  - `ELEVENLABS_API_KEY` — **não** populada (TTS default é OpenAI).
- [ ] **ADC do Google funcionando**:
  `gcloud auth application-default print-access-token` retorna token.
  Se F0.1 escolheu Vertex como default: `gcloud auth application-default
  set-quota-project ai-production-432511`.
- [ ] **Áudio de teste descartável** gravado: ~30–60s, narração inventada
  **sem a filha**, sem conteúdo sensível. Tema neutro (raposa que descobre
  uma poça d'água, gato que vê a lua, etc.).
- [ ] `uv run contadinhos new smoke-e2e` → story criada em
  `stories/<YYYY-MM-DD>-smoke-e2e/`. Copiar o áudio gravado pra
  `stories/<YYYY-MM-DD>-smoke-e2e/audio.m4a`.

### Fase 2 — Gate barato real (~$0.10) — obrigatório antes do Veo

> Equivalente à Fase D de Sprint 5b. **Travar gasto Veo até este gate
> passar.** O custo está em `OPENAI`/`GOOGLE` keys (TTS + pré-gate
> exercitados com payload pequeno).

- [ ] Confirmar `tests/integration/test_real_providers.py` cobre:
  - `OpenAITranscriber` real (áudio pequeno fixture)
  - `OpenAIRoteirista` real (transcript pequeno)
  - `GeminiPreGateAuditor` real (roteiro pequeno)
  - `OpenAITTS` real (1 cena curta)
  - `GeminiTTS` real (1 cena curta)
  - `NanoBananaImageGenerator` real (1 imagem-chave, 1 candidata)
  - **Não** exercita Veo nem pós-gate (custo).
- [ ] `uv run pytest -m real_provider` verde.
- [ ] Custo real registrado: somar `cost_ledger.json` das stories de teste
  + checar fatura OpenAI/Google. Esperado: **< $0.20**.
- [ ] Se contract divergir (formato real ≠ Fake), atualizar
  `tests/contracts/<interface>.py` **antes** de seguir pra Fase 3.

### Fase 3 — E2E real capado (<$1 Veo)

> Equivalente à Fase E de Sprint 5b. Primeiro vídeo real do projeto.
> Upload **privado** — não vira público até auditoria de compliance
> (`sprints.md` Sprint 5 §Tasks).

- [ ] `uv run contadinhos script stories/<id> --target-duration-s 15`
  (~3–4 cenas de ~4–5s → Veo Lite ~$0.30–0.80, capado pelo `target_duration_s`).
- [ ] `uv run contadinhos run stories/<id>` → para em `pick_images`.
- [ ] **Pick manual de verdade** (não `--auto-pick`):
  - Abrir cada `stories/<id>/images/<img_id>/candidate_*.png` no Preview/Finder
  - `uv run contadinhos pick stories/<id> <img_id> -c <n>` por imagem-chave
- [ ] `uv run contadinhos run stories/<id>` segue:
  - `run_video` (Veo Lite) → `clips/scene_NN.mp4` × N
  - `run_tts` (OpenAI) → `audio/narration_NN.wav` × N
  - `run_assemble` (ffmpeg) → `final.mp4` (sem música/legenda — Sprint 4.5+)
  - `run_publish` → pós-gate (Gemini multimodal sobre `final.mp4`) → upload
    YouTube **privado**
- [ ] `next_action(stories/<id>) == "done"` ✅
- [ ] `cost_ledger.json` com entradas ≠ 0 em todas etapas
- [ ] `policy_check_pre.json` + `policy_check_post.json` com `verdict == "ok"`
- [ ] Vídeo visível em [studio.youtube.com](https://studio.youtube.com) como
  **privado**, made-for-kids ativo, título via template, descrição com
  `sinopse_curta`.

## Como implementar (TDD)

**Fase 0** — refator de auth, principalmente provider-side. Contract tests
existentes (`tests/contracts/{pre_gate,post_gate,image_generator,
video_generator}.py`) cobrem o comportamento; **não duplicar lógica de
teste**, só atualizar fixtures se assinatura do construtor mudou.

- Se F0.1 = toggle plugável (A): teste novo
  `tests/unit/test_google_client_toggle.py` cobre:
  - `auth_mode=vertexai` instancia `Client(vertexai=True, project=..., location=...)`
  - `auth_mode=api_key` instancia `Client(api_key=...)` lendo `api_key_env`
  - `auth_mode` inválido levanta `RuntimeError` claro
- Se F0.1 = hard switch (B): teste só pro caso `vertexai`; rejeição de
  `api_key` continua.

**Fases 1–3** — operacionais e smoke. Sem TDD red-green-refactor, mas
**Fase 2 é o gate barato** que valida contracts contra providers reais:
se Real cospe formato diferente do Fake, atualizar **contract**.

**Boas práticas a observar:**

- Pre-flight check de custo Veo (`decisions.md §11.2`) **continua não
  implementado**. Fase 3 limita gasto via `target_duration_s=15` apenas —
  abortar story se passar do estimado nominal é Sprint 7+. Se você for
  testar story mais longa, calcular manualmente antes.
- Pós-gate hoje **bloqueia upload** se `verdict=review_required`
  (`pipeline.PipelineBlocked`). Esperado em Fase 3: `verdict=ok`. Se vier
  `review_required`, abrir as flags em `policy_check_post.json`, decidir
  se é falso-positivo ou se precisa regenerar cena.
- **Ledger é nominal**, não faturado — não usar como métrica de custo
  real. Confirmar valor em [console.cloud.google.com/billing](https://console.cloud.google.com/billing)
  + [platform.openai.com/usage](https://platform.openai.com/usage).

## Files entregues

- **Fase 0:**
  - `config/providers.yaml` (auth_mode atualizado conforme F0.1)
  - `src/contadinhos/core/google/client.py` (helper Vertex; com branch
    `api_key` se F0.1 = toggle)
  - `src/contadinhos/core/{images,video,policy}/<provider>.py` (consomem
    `vertex_client()` em vez de `api_key=` no construtor)
  - `src/contadinhos/frontends/cli/deps.py` (reconciliação Sprint 5b + Vertex)
  - `tests/unit/test_real_deps_wiring.py` (atualizado)
  - `tests/unit/test_{nano_banana,veo,pre_gate_logic,post_gate}.py`
    (assinaturas atualizadas)
  - `tests/integration/test_real_providers.py` (cobre Vertex)
  - (se toggle) `tests/unit/test_google_client_toggle.py`
  - Docs: `decisions.md §5/§7.2/§11.5/§19`, `sprints.md` Sprint 0,
    `sprint5-setup.md §1`, `.env.example`, `CONTEXT.md` (pós-gate),
    `CLAUDE.md` (Auth Google)
- **Fase 1:** nenhum arquivo de código novo. `.env` populado, story de
  teste criada com `audio.m4a` real.
- **Fase 2:** nenhum arquivo novo se contracts já cobrem; senão atualizar
  `tests/contracts/<interface>.py`.
- **Fase 3:** uma story real (`stories/<YYYY-MM-DD>-smoke-e2e/`) com
  `final.mp4`, `upload_result.json`, `cost_ledger.json` populados.
  Arquivo `docs/calibration-log.md` (novo) com observações do primeiro vídeo
  — opcional mas recomendado (vira corpus pra Sprint 7).

## Definition of Done

✅ Fase 0: refator Vertex commitado no `main`, suíte verde, docs
reconciliadas em **uma passada conexa** (sem doc-drift entre arquivos).

✅ Fase 1: `gcloud auth application-default print-access-token` retorna;
`~/.contadinhos/youtube_token.json` existe; `.env` válido; story
`smoke-e2e` criada com `audio.m4a`.

✅ Fase 2 (gate barato): `uv run pytest -m real_provider` verde; custo real
observado **< $0.20** somando OpenAI + Google.

✅ Fase 3 (E2E real): `Story.next_action() == "done"` para a story
`smoke-e2e`. `upload_result.json` com `videoId` real (privado).
`final.mp4` reproduz no QuickTime. Vídeo aparece em studio.youtube.com.
Gasto Veo real **< $1**, verificado na fatura (não no ledger).

✅ Contract `TTSProvider`, `ImageGenerator`, `VideoGenerator`,
`PreGateAuditor`, `PostGate` revalidados contra implementações reais. Se
algum divergiu do Fake, **contract** foi atualizado (não só o caso
concreto).

✅ Smoke real (§20.6 de `decisions.md`): documentar em
`docs/calibration-log.md` (1 entrada) o que **divergiu** entre Fake e
Real, e o que ajustar pro próximo vídeo (prompt, voz, tier Veo).

## Pendências / armadilhas conhecidas

- **Conflito Vertex × Sprint 5b em `deps.py`**: o stash remove `_require_env
  ("GOOGLE_GENERATIVE_AI_API_KEY")` incondicionalmente; Sprint 5b já o
  removeu desse jeito + tornou ElevenLabs condicional. Resultado final
  esperado: `_real_deps()` exige **só** keys de OpenAI (sempre) + TTS
  provider ativo (mapa provider→env, excluindo Google que vai por ADC).
- **`auth_mode` default** ainda é decisão aberta. Se F0.1 = toggle,
  recomendo `auth_mode: vertexai` no commit do main (já que o crédito
  Google está no projeto Vertex `ai-production-432511`). Pode reverter pra
  `api_key` por config sem mexer no código.
- **Quota Vertex AI**: projeto `ai-production-432511` tem quota default.
  Vídeos de 8s × N cenas com Veo Lite cabem; se a fatura mostrar quota
  hit, considerar `gcloud quotas` antes de subir tier pra Fast.
- **Pós-gate inline bytes ≤ 18 MB**: vídeos de 60–90s @ 1080p cabem; se
  algum dia a duração média subir, virar GCS path (galho `decisions.md §19`).
- **Veo Lite é status `preview`**: pode mudar/deprecar. Aceito por decisão.
- **`auth-youtube` interativo**: o browser precisa abrir. Se rodar em
  máquina headless (ex.: VPS Telegram da Sprint 6), o flow precisa ser
  feito no Mac local e o token copiado.
- **Áudio de teste descartável**: nunca o real da filha em testes. Mesmo
  que privado, o áudio aparece em fatura/logs Google.
