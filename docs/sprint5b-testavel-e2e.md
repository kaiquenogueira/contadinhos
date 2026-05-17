# Sprint 5b — Tornar o pipeline real executável ponta-a-ponta

> Ponte **Sprint 5 → Sprint 7**. Independente de Sprint 6 (Telegram). O
> código das etapas reais já existe (Sprints 1–5); o que falta é destravar
> o caminho real ponta-a-ponta sem ElevenLabs, com custo Veo controlado, e
> validá-lo com uma story de verdade. Saída observável: uma story real
> chega a `next_action == done` (upload **privado**).
>
> Plano resolvido na grelha de 2026-05-17. **Por quê** de cada decisão:
> memória `project_testavel_e2e`; princípios em `decisions.md §20`.

## Pré-requisitos

- Sprints 1–5 ✅ (impls reais de todas as etapas existem; suíte 107 verde)
- Keys **em mãos**: `OPENAI_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`.
  ElevenLabs **descartada** por decisão (sem key, sem plano de pegar)
- Google Cloud: Generative Language API **ON**, YouTube Data API v3 **ON**
  (confirmado na grelha)
- `~/.contadinhos/client_secret.json` presente; **token ainda não** cunhado
- `ffmpeg`/`ffprobe` instalados ✅

## Tasks

### Fase A — Destravar TTS sem ElevenLabs (código, TDD)

- [x] **Fix bloqueador** em `frontends/cli/deps.py::_real_deps()`: hoje
  `_require_env("ELEVENLABS_API_KEY")` roda **incondicional**
  ([deps.py:87](../src/contadinhos/frontends/cli/deps.py)) → sem a key,
  `_real_deps()` morre no boot mesmo com TTS=OpenAI. Tornar a exigência de
  key **condicional ao provider de TTS selecionado** em
  `config/providers.yaml::tts.provider`.
- [x] `core/tts/openai.py::OpenAITTS` — espelha `elevenlabs.py`. Usa
  `client.audio.speech.create(model="gpt-4o-mini-tts", voice=…,
  input=text, instructions=…, response_format="wav")`. `@retryable("tts")`.
  Atributo `.model` pro `_provider_id` do ledger.
- [x] `core/tts/gemini.py::GeminiTTS` — Gemini 2.5 Flash TTS via
  `google-genai`, mesma `GOOGLE_GENERATIVE_AI_API_KEY`. `@retryable("tts")`.
- [x] `config/voices.yaml`: voz default + **instrução de estilo** pt-BR
  ("narrador de história infantil, caloroso, pausado, tom de livro
  ilustrado em aquarela") — dado em config, nunca f-string no código.
- [x] `config/providers.yaml`: `tts.provider` selecionável
  (`openai` | `gemini` | `elevenlabs`); default = `openai`.
- [x] Wire em `_real_deps()`: instancia o TTS conforme `tts.provider`.

### Fase B — Política de custo de vídeo (config, sem código)

- [x] `config/providers.yaml`: `video.model: veo-3.1-lite-generate-preview`.
- [x] Comentário de política no YAML: **Lite = plumbing/dev**, **Fast =
  teto de produção**, **Standard morto** (arena ELO: Fast≈Standard dentro
  do erro, 4× o preço), Seedance 2.0 = galho `decisions.md §19` (só
  reabrir se consistência da Clarinha no Veo decepcionar em I2V real).

### Fase C — Setup manual externo (operacional)

- [ ] OAuth consent screen: User Type **External**, test user
  `plataformaencantrip@gmail.com` (`docs/sprint5-setup.md §2`).
- [ ] `uv run contadinhos auth-youtube` → cunha o token. **Verificar o
  path real** que `core/upload/auth.py::token_path()` usa
  (`~/.contadinhos/youtube_token.json` no código vs `.secrets/…`
  mencionado em `sprints.md` Sprint 5 — `auth.py` é a fonte de verdade,
  reconciliar a doc se divergir).
- [ ] `.env` a partir de `.env.example`: só `OPENAI_API_KEY` +
  `GOOGLE_GENERATIVE_AI_API_KEY` (ElevenLabs **não** necessária).
- [ ] Gravar áudio inventado descartável ~30-60s (sem a filha, sem
  conteúdo sensível). `uv run contadinhos new smoke-e2e` → dropar como
  `audio.m4a` na story criada.

### Fase D — Gate barato (smoke real, ~$0.10) — obrigatório antes do Veo

- [x] Atualizar `tests/integration/test_real_providers.py`: cobrir
  `OpenAITTS` + `GeminiTTS` reais; condicionar/remover o teste ElevenLabs.
- [ ] `uv run pytest -m real_provider` verde. **Só passa → libera Fase E.**

### Fase E — E2E capado real (<$1 Veo)

- [ ] `uv run contadinhos script stories/<id> --target-duration-s 15`
  (~3-4 cenas curtas → render Veo Lite < $1).
- [ ] `uv run contadinhos run stories/<id>` → para em `pick_images`.
- [ ] Inspecionar as 4 candidatas Nano Banana; `contadinhos pick
  stories/<id> <img_id> -c <n>` (pick **manual de verdade**).
- [ ] `contadinhos run stories/<id>` segue → `final.mp4` → pós-gate →
  `publish` (privado, `publish_mode=private_only`).

## Como implementar (TDD)

**Testes (escrever primeiro):**

1. `tests/unit/test_deps_tts_key_condicional.py`
   - `test_real_deps_nao_exige_elevenlabs_quando_provider_openai` —
     env sem `ELEVENLABS_API_KEY`, `providers.yaml::tts.provider=openai`
     → `build_deps(False)` **não** levanta
   - `test_real_deps_exige_key_do_provider_ativo` — `tts.provider=openai`
     sem `OPENAI_API_KEY` → erro claro nomeando a key certa
2. `tests/unit/test_openai_tts.py`
   - `class TestOpenAITTS(TTSProviderContract)` — subclassa o contract
     existente (`tests/contracts/tts_provider.py`); mesma asserção do Fake
   - `test_openai_tts_aborta_sem_texto` — texto vazio → `ValueError`
3. `tests/unit/test_gemini_tts.py`
   - `class TestGeminiTTS(TTSProviderContract)` — idem
4. `tests/integration/test_real_providers.py` (modificado)
   - `test_real_openai_tts_curto` `@pytest.mark.real_provider`
   - `test_real_gemini_tts_curto` `@pytest.mark.real_provider`

**Implementação:**

`OpenAITTS`/`GeminiTTS` são wrappers finos espelhando `ElevenLabsTTS`
(client lazy via `_ensure_client`, `synthesize(text, voice_id,
output_path)` escrevendo WAV). Fix de `_real_deps()`: ler
`load_config("providers")["tts"]["provider"]`, exigir só a key daquele
provider (mapa provider→env). Fakes em `tests/fakes/` **não mudam** — o
contract `TTSProviderContract` já cobre os dois novos.

**Boas práticas a observar:**

- Voz + instrução de estilo em `config/voices.yaml`; provider em
  `config/providers.yaml`. Mudar config muda comportamento sem tocar
  código (testar isso). Tier de vídeo idem (`decisions.md §4`, memória
  `isolar_config_mutavel`).
- `@retryable("tts")` nas chamadas de rede (padrão `§8.8`).
- Red-green-refactor: integração-com-Fake antes de unit (`§20.2`);
  um teste = uma asserção; nome descreve comportamento.

## Files entregues

- `src/contadinhos/core/tts/openai.py`, `src/contadinhos/core/tts/gemini.py`
- `src/contadinhos/frontends/cli/deps.py` (modificado: key condicional + wiring)
- `config/providers.yaml` (tts.provider, video.model→lite, política de tier)
- `config/voices.yaml` (voz default + instrução de estilo pt-BR)
- `tests/unit/test_deps_tts_key_condicional.py`
- `tests/unit/test_openai_tts.py`, `tests/unit/test_gemini_tts.py`
- `tests/integration/test_real_providers.py` (modificado)
- *(Fakes e `tests/contracts/tts_provider.py` reaproveitados, sem mudança)*

## Definition of Done

✅ Suíte verde sem custo: `uv run pytest -m "not real_provider"`
(107 anteriores + novos TTS/deps).

✅ `_real_deps()` monta **sem** `ELEVENLABS_API_KEY` quando
`tts.provider ∈ {openai, gemini}`.

✅ **Gate barato** verde: `uv run pytest -m real_provider` exercita
OpenAI + Gemini TTS reais (~$0.10) — passou antes de qualquer gasto Veo.

✅ Uma story real atinge `next_action == done`: `upload_result.json` com
`videoId` (privado), `final.mp4` valida no `ffprobe`, `cost_ledger.json`
com entradas ≠ 0, `policy_check_pre.json`/`policy_check_post.json` com
`verdict == "ok"`.

✅ `pick_images` exercitado **manual de verdade** (não `--auto-pick`).

✅ Gasto Veo do 1º E2E **< $1**, verificado na conta Google — **não** no
ledger (ledger é nominal/placeholder Sprint 2; custo real só na fatura).

✅ **Smoke real (§20.6 de `decisions.md`):** contract `TTSProvider`
revalidado contra OpenAI/Gemini reais. Se o comportamento/IO divergir do
Fake, **atualizar o contract** (não só o caso concreto).

## Pendências / armadilhas conhecidas (não esquecer)

- **Ledger é nominal**, não faturado (`pipeline._step_cost` lê estimativas
  fixas de `config/budget.yaml`; `response.usage` real é Sprint 7). Não
  ler o ledger do 1º E2E como custo real.
- **Veo Lite é `preview`** (galho `decisions.md §19`) — pode mudar/
  deprecar. Aceito por decisão do projeto.
- **Arena ELO inclui áudio** que o pipeline descarta (narração vem do TTS
  separado) — não sobre-rotacionar em leaderboard pra escolha de vídeo;
  decidir tier de produção com clipe I2V real da Clarinha na mão.
- **A/B de TTS pt-BR** (OpenAI vs Gemini vs eventual ElevenLabs/Hume)
  fica para depois do pipeline verde — decisão de voz de produção por
  evidência (mini-first), fora do escopo desta sprint.
