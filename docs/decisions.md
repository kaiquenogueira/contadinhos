# contadinhos — decisões de design

> Documento mestre do **"por quê"**. Cada decisão fechada aqui foi grelhada explicitamente.
> O **"como executar"** mora em [`sprints.md`](./sprints.md).
> Pendências no fim do arquivo são os galhos que ainda não foram resolvidos.
>
> **Legenda de autoria das decisões:**
> - 👤 = decidido por Kaique em sessão de grelha
> - 🤖 = decidido automaticamente nesta sessão (2026-05-04) com aprovação
>   genérica pra preencher os galhos abertos. **Toda decisão 🤖 é candidata
>   a revisão** — se algo soar errado, abrir nova grelha pra reabrir.
> - 🤖→👤 = proposto 🤖 em sessão e aprovado 👤 em seguida (vira fechado).

## Premissa

Kaique conta histórias para a filha quase todos os dias e quase sempre inventa
novas. Quer transformar essas histórias em vídeos animados com IA generativa
de vídeo (Veo 3.1, Kling, Runway etc.) e publicar automaticamente em
plataformas como YouTube.

---

## 1. Conteúdo e privacidade

| Decisão | Valor |
|---|---|
| Saída final | **Anônima por design**: sem voz do pai, sem identificação visual, sem áudio original |
| Audiência | Canal **público desde o dia 1**, sem pressão de métrica/engajamento. Filha também re-assiste via **YouTube clássico** (conta do pai num device da casa) — não YouTube Kids app. Decisão revisada em 2026-05-06: simples por enquanto, reabrir se ficar incômodo. |
| Tom das histórias | Aventuras tranquilas, sem violência/medo |
| Personagem "filha" no roteiro | 🤖→👤 **Clarinha** — fictício fixo. Aparece em texto/narração. |
| Aparência da filha real | **Nunca** nos prompts visuais. Personagem-menininha gerada genérica. |
| Voz da filha real (gravada na captura) | **Nunca** vai pro vídeo. Só a transcrição é consumida. |

**Por quê anônimo:** simplifica todo o pipeline (mata trilho duplo família/público,
mata anonimização de áudio, mata revisão LGPD/COPPA caso-a-caso). Custo: o "papai
contou" se traduz só pelo enredo no vídeo final, não pela voz/cara.

---

## 2. Forma do vídeo

| Item | Decisão |
|---|---|
| Duração | **Adaptativa 60–90s.** Cada vídeo cobre o enredo no menor tempo que respeita a história. >90s vira "Parte 1 / Parte 2". |
| Narração | **TTS pt-BR feminino** infantil-amigável (ElevenLabs como provedor padrão) |
| Texto na tela | Sim, gerado a partir do roteiro (legenda + reforço de leitura pra outras famílias) |
| Música | Suave, fundo. YouTube Audio Library, curadoria de 5–10 faixas em rodízio |
| Estilo visual | **Aquarela / livro infantil ilustrado**, fixo. String de estilo única em todo prompt |
| Output | 1080p MP4 / H.264 / AAC / 30fps |

**Por quê duração 60–90s:**
- Cabe atenção de 3 anos.
- IA atual gera clipes de 5–10s; 60–90s = ~10 clipes encadeados, risco de inconsistência tolerável.
- Custo por vídeo manejável (ver §6).

**Por quê aquarela:** modelos de vídeo IA reproduzem aquarela com facilidade,
glitches viram "estilo", combina com aventuras tranquilas, identidade de canal
estável e barata.

---

## 3. Pipeline

```
[história contada à noite]
        │
        ▼ gravação de áudio (celular)
        │
        ▼ Whisper → transcrição completa, sem filtro
        │
        ▼ LLM roteirista (recebe transcrição + target_duration_s)
        │   filtra ruído pessoal e trechos fora-do-enredo
        │
        ▼ Roteiro JSON ─┐
        │              │ revisão humana (~2–5 min)
        ▼              │
[lista de imagens-chave a gerar]
        │
        ▼ Nano Banana (Gemini 2.5 Flash Image) — 4 candidatas cada
        │   revisão humana (~30s/imagem)
        │
        ▼ Imagens-chave (incl. 1 que vira miniatura YouTube)
        │
        ▼ Para cada cena:
        │     - se tem personagem  → I2V (first-frame = imagem-chave)
        │     - se é paisagem pura → T2V
        │   via VideoGenerator (Kling / Veo 3.1 / Runway intercambiáveis)
        │
        ▼ Clipes de cena
        │
        ▼ TTS (ElevenLabs via TTSProvider) por cena
        │
        ▼ FFmpeg: concat + crossfade + mix audio + drawtext + música
        │
        ▼ MP4 final
        │
        ▼ Policy check  (PENDENTE — §"Pendências")
        │
        ▼ Upload YouTube  (PENDENTE — §"Pendências")
```

### 3.1 Contrato de roteiro (saída do LLM roteirista)

```json
{
  "titulo": "...",
  "duracao_total_s": 78,
  "personagens": [
    { "id": "raposa", "descricao_visual": "uma raposa laranja amigável, olhos grandes, expressão curiosa" },
    { "id": "menininha", "descricao_visual": "uma menininha de cabelo castanho cacheado, vestido amarelo" }
  ],
  "imagens_chave": [
    { "id": "raposa", "prompt": "..." },
    { "id": "menininha", "prompt": "..." },
    { "id": "elenco", "prompt": "raposa e menininha juntas..." }
  ],
  "cenas": [
    {
      "idx": 1,
      "modo": "i2v",
      "imagem_chave_ref": "raposa",
      "prompt_visual": "...",
      "narracao": "Era uma vez uma raposa muito curiosa...",
      "duracao_s": 7
    },
    { "idx": 2, "modo": "t2v", "prompt_visual": "...", "narracao": "...", "duracao_s": 6 }
  ]
}
```

Esse JSON é o **contrato entre etapas**. Cada etapa downstream é função pura sobre ele.

### 3.2 Continuidade entre cenas: sem chaining por padrão

🤖→👤 **Decidido (sessão 2026-05-06):** **sem chaining de last-frame** por
padrão. Cada cena é um clipe independente:

- Cena I2V parte da `imagem_chave_ref` (cópia do `chosen.png` do personagem).
- Cena T2V parte só do `prompt_visual` (nenhum first-frame).
- Ffmpeg só faz concat na montagem; **nada** de extrair last-frame da cena N
  pra alimentar cena N+1.

Flag `video.chain_first_frame` em `config/pipeline.yaml` mantida como opt-in
experimental — desabilitada por padrão.

**Por quê sem chain:**
- **Erro composto.** 10 cenas em sequência = 10 passos de degradação visual
  (compressão H.264 + drift do Veo). Personagem na cena 1 != cena 7 != cena
  10. Aquarela "pasteliza" rápido. Modo de falha tipo "vídeo todo derrete"
  só aparece na Sprint 4 — caro pra descobrir.
- **Identidade aceita o salto.** §2 fixou estilo "aquarela / livro infantil
  ilustrado". Salto visual entre cenas vira "virar página" — narrativamente
  coerente com livro infantil, não distrai criança de 3 anos.
- **Continuidade de personagem já está resolvida** pelas imagens-chave.
  `imagem_chave_ref` garante "mesma raposa" em todas as cenas I2V dela.
- **Paralelizável.** Sem dependência sequencial entre cenas, geração de
  clipes paraleliza trivialmente no futuro (otimização posterior).
- **Mais barato em pipeline.** Sem passo de extract-last-frame entre cenas.

Reabrir como galho em §19 se Sprint 7 mostrar "salto visual entre cenas
quebra a história" como dor real.

---

## 3.3 Política de tier de modelo: "mini + prompt cuidadoso" como default

🤖→👤 **Decidido (sessão 2026-05-07):** sempre que a tarefa é
**bem-definida** (input estruturado ou semi-estruturado, output com schema
fechado, regras explícitas de estilo), default é **tier mini do provider**.
Tier flagship só entra se o mini provar insuficiente nos primeiros 5
vídeos da calibração (Sprint 7).

**Aplicação:**

| Etapa | Default mini | Flagship fallback | Por quê mini funciona |
|---|---|---|---|
| Roteirista (`gpt-5-mini`) | ✅ | `gpt-5.5` | Schema fechado, style guide explícito, transcript com sinal claro |
| Pré-gate (`gemini-2.5-flash`) | ✅ | `gemini-2.5-pro` ou `gpt-5.5` | Categorias enumeradas, prompt de auditor estrito |
| Pós-gate (`gemini-2.5-flash`) | ✅ | `gemini-2.5-pro` | Mesmo argumento; multimodal `flash` é capaz |
| Transcrição (`gpt-4o-transcribe`) | já é tier baixo de custo ($0,006/min) | `gpt-4o-transcribe` (já é) ou local Whisper-large | Qualidade upstream é gate; **não** descer pra `mini-transcribe` |

**Princípios de prompting que tornam o mini suficiente** (aplicar em todos
os prompts em `config/prompts/`):

1. **System prompt explícito:** persona + tarefa + restrições + formato em <100 linhas. Nada de "seja útil"; tudo com restrição clara.
2. **Few-shot examples** quando o output é criativo (ex.: 1–2 roteiros de exemplo no system prompt do roteirista).
3. **Schema fechado** com `response_format=json_schema` (OpenAI) / `response_schema` (Gemini) sempre que o output é estruturado.
4. **Style guide externalizado** em `config/prompts/style.md`, injetado como variável no system prompt — versionado, calibrável.
5. **Constraint negativos** explícitos ("nunca", "se X, retorne Y", "se duvidar, flag em vez de aprovar").

**Quando subir pra flagship:** se a calibração (Sprint 7) mostrar (a) >2 falsos-positivos do pré-gate em 10 vídeos, OU (b) >1 roteiro com cena ilógica/incoerente em 10 vídeos, **antes** de mexer no prompt. Critério inverso: subir só se prompting bem-feito não bastar.

**Why:** prompt engineering escala linear com esforço; modelo flagship escala em custo. Pra projeto on-demand de 10–15 vídeos/mês, otimizar prompt é melhor investimento que pagar 15× a mais por modelo.

---

## 4. Princípios arquiteturais

- **Provider-agnostic** em vídeo (`VideoGenerator`) e TTS (`TTSProvider`). Não ficar refém de Kling, Veo, ElevenLabs.
- **Roteiro JSON é o contrato** entre etapas. Cada etapa: função pura sobre o JSON.
- **Stack Python** (Whisper, OpenAI/Anthropic SDKs, FFmpeg via `ffmpeg-python` ou subprocess, SDKs dos provedores).
- **Revisão humana mínima por vídeo:** ~30s/imagem-chave + ~2–5 min roteiro. Acima disso, pipeline não escala pra "quase diário".
- **Custo previsível:** ver §6. Teto por vídeo, alerta se ultrapassar.
- **MVP sequencial em fases curtas validáveis** (a definir — §Pendências).
- **Config isolada do código:** todo valor que evolui com aprendizado
  (categorias, prompts de judge, severidades, lista de estilos, voz
  default, modelo default, teto de custo, etc.) mora em config externa.
  Lógica pura no código; parâmetros em YAML/JSON/TOML. Secrets em `.env`.

---

## 5. Decisões de ferramenta

| Etapa | Escolha primária | Abstração? | Por quê |
|---|---|---|---|
| Captura | Gravador do celular | Não | Trivial |
| STT | 🤖→👤 (2026-05-07): **OpenAI `gpt-4o-transcribe`** (sucessor do `whisper-1`, ~22% menos WER, melhor pt-BR em áudio bagunçado). Fallback barato: `gpt-4o-mini-transcribe`. | Não | Padrão de fato; provider abstrai pouco aqui (transcript é texto puro) |
| Roteirização | 🤖→👤 (2026-05-07, revisado 2×): **OpenAI `gpt-5-mini`** padrão — $0,25/$2 por 1M tokens (15× mais barato que gpt-5.5), 400K context. Tarefa é bem-definida (transcript livre → JSON estruturado seguindo schema + style guide), prompting cuidadoso compensa o tier menor. Fallback qualidade: `gpt-5.5` (1 line config). Custo por vídeo: ~US$0,005. | Sim, baixo custo | Roteiro = JSON, qualquer LLM bom serve. `core/script/llm.py` recebe model via config. |
| Imagem-chave | 🤖→👤 (2026-05-07, revisado pós-research): **Nano Banana 2** (`gemini-3.1-flash-image-preview`) — substitui o `gemini-2.5-flash-image` original. Nano Banana 2 traz **consistência de até 5 personagens** num workflow, endereçando direto o galho de "Clarinha drifar entre vídeos" (§19). Status preview aceito (galho §19). | Sim, baixo custo (`ImageGenerator`) | 4 candidatas, escolha humana. Mesma família Google = um SDK (`google-genai`), créditos compartilhados. |
| Geração de vídeo | 🤖→👤 (2026-05-07, revisado pós-research): **Veo 3.1** (`veo-3.1-generate-preview`) — substitui `veo-3.0-generate-001`. Linha mais recente, melhor qualidade. Variantes plugáveis: `veo-3.1-fast-generate-preview` (mais rápido), `veo-3.1-lite-generate-preview` (mais barato). Status preview aceito. Kling 2.0 e Runway continuam plugáveis como alternativas. | **Sim, `VideoGenerator`** | Provider-agnostic é invariante. Veo entra como default pelo crédito; abstração intacta. |
| **Auth Google (Veo + Nano Banana + Gemini multimodal)** | 🤖→👤 (sessão 2026-05-07): **Gemini API direto via `GOOGLE_GENERATIVE_AI_API_KEY`** — não Vertex AI + ADC. Crédito Google está associado a essa key. | — | Uma única chave atende os 3 serviços Google (Veo, Nano Banana, Gemini Flash do pós-gate). SDK é o mesmo `google-genai` mas instanciado com `genai.Client(api_key=...)` em vez de `genai.Client(vertexai=True)`. Vertex AI fica como caminho futuro (galho §19). |
| TTS | **ElevenLabs** padrão | **Sim, `TTSProvider`** | Expressividade vocal é metade do produto; abstração permite trocar |
| Música | YouTube Audio Library curada | Não | Grátis, copyright-safe, identidade por reuso |
| Montagem | FFmpeg programático em Python | Não | Stack já é Python; texto, mix, concat triviais |
| Output | 1080p MP4 H.264 / AAC 30fps | Não | Padrão YouTube |

---

## 6. Estimativas de custo

> ⚠️ **Estimativas de ordem de grandeza.** Antes de fechar orçamento mensal,
> confirmar com tabela atual de cada provedor.

Por vídeo de 75s:

| Item | Custo aprox. |
|---|---|
| Transcrição (`gpt-4o-transcribe`, ~3min áudio @ $0,006/min) | ~US$0,02 |
| LLM roteirista (`gpt-5-mini`, ~3K input + 2K output @ $0,25/$2 por 1M) | ~US$0,005 |
| Pré-gate (`gemini-2.5-flash`, §7.1) | ~US$0,005–0,02 |
| Imagens-chave Nano Banana (1–3 × 4 candidatas, ~US$0,039/img) | ~US$0,12–0,47 (nominal; em crédito Google) |
| Vídeo I2V/T2V (~10 cenas × 8s) — **Kling** | US$8–18 |
| Vídeo I2V/T2V — **Veo 3.1** (alternativa cara) | US$30–50 |
| TTS ElevenLabs (~75s narração) | US$0,15–0,30 |
| Música | US$0 |
| Montagem FFmpeg | US$0 |
| Upload YouTube | US$0 |
| Policy check (LLM multimodal) | US$0,05–0,20 |
| **Total / vídeo (Kling)** | **~US$10–20** |
| **Total / vídeo (Veo 3.1)** | **~US$30–55** |

Se o ritmo for ~quase diário (~30 vídeos/mês):
- Com Kling: **US$300–600/mês**
- Com Veo: **US$900–1650/mês**

---

## 7. Policy check (gate de publicação)

Decisão: **camada dupla de checagem**, com **bloqueio sempre que reprovar** (sem auto-retry).

### 7.1 Pré-gate (texto, no roteiro)

🤖→👤 **Decidido (sessão 2026-05-06):** **chamada LLM separada**, depois do
roteirista. **Não** roda dentro do mesmo prompt do roteirista.

| Item | Decisão |
|---|---|
| Modelo | 🤖→👤 (2026-05-07): **`gemini-2.5-flash`** via `GOOGLE_GENERATIVE_AI_API_KEY`. Provider **diferente do roteirista** (que é OpenAI gpt-5) = independência real, sem nova key (já temos). |
| Persona | Auditor estrito de conteúdo infantil (prompt em `config/prompts/pre_gate.md`) |
| Input | Roteiro JSON completo (output do roteirista) |
| Output | `policy_check` block (mesmo schema do §7.4) — sobrescreve campo no `roteiro.json` |
| Custo nominal | ~US$0,005–0,02 por vídeo |

**Por quê separar do roteirista** (decisão revisada em 2026-05-06):
- O LLM roteirista tem **incentivo estrutural de produzir o deliverable**. Auto-flagar é auto-sabotagem; viés sistemático contra reprovar.
- O modelo não tem distância crítica do que acabou de gerar; "isso que eu escrevi tá bem" é literal.
- Pós-gate (§7.2) já roda como chamada/modelo separado — mesma lógica deve valer pro pré.
- Custo extra (~US$0,02) é desprezível vs custo do vídeo (~US$30–55) e vs custo de descobrir o problema só no pós-gate (já tem MP4 montado, foi caro).
- "Mesmo modelo, persona diferente, chamada separada" basta — não precisa de modelo de família distinta. O que muda é o framing.

Pega risco **narrativo**: medo, violência, tema adulto, linguagem.

### 7.2 Pós-gate (multimodal, no MP4 final)

Roda **antes do upload**, em LLM multimodal sobre frame samples + áudio
do MP4 já montado. Custo ~US$0,05–0,20.

Pega modos de falha **visuais** que o pré-gate não vê:
- glitch de IA (mãos com 7 dedos, rostos distorcidos, anatomia errada)
- vibe sombria emergente (paleta, expressões, clima) que o roteiro
  inocente não previa

### 7.3 Política de reprovação

| Resultado | Ação |
|---|---|
| Pré-gate `ok` | Segue: aprova roteiro, gera imagens-chave |
| Pré-gate `review_required` | **Bloqueia.** CLI mostra flags + pede decisão humana (editar roteiro / aprovar override / abandonar) |
| Pós-gate `ok` | Segue: faz upload |
| Pós-gate `review_required` | **Bloqueia.** CLI mostra clipe + flags + pede decisão (regenerar cena específica / refazer vídeo / abandonar / aprovar override) |

**Sem auto-retry.** Justificativas:
- Projeto é on-demand, ~1 vídeo/dia, humano já no loop em outros pontos.
- Auto-retry inflaciona custo silenciosamente (cena Kling regenerada ~US$1–2 cada).
- Calibrar threshold de severity exige LLM-as-judge estável — vai virar tuning eterno.

### 7.4 Schema canônico

Campo dentro do roteiro JSON, sobrescrito/aumentado pelo pós-gate:

```json
"policy_check": {
  "verdict": "ok" | "review_required",
  "severity": "low" | "medium" | "high",
  "flags": [
    {
      "category": "medo" | "violencia" | "tema_adulto" | "linguagem"
                | "glitch_visual" | "vibe_sombria" | "outro",
      "description": "personagem 'quase foi pego pelo lobo'",
      "scene_idx": 4
    }
  ],
  "reviewer_note": null
}
```

- `severity` é **informativa**, não muda comportamento (humano sempre decide).
- `scene_idx` é `null` quando o flag é difuso/global.
- `reviewer_note` é preenchido na revisão humana e vira **histórico** —
  depois de 5–10 vídeos, dá pra ver padrões reincidentes e ajustar prompts.
- Mesmo schema para pré e pós; pós-gate **mescla** flags em vez de sobrescrever.

### 7.5 Isolamento de config (princípio geral)

Para facilitar manutenção/recalibração, **tudo que muda com aprendizado**
mora em config externa, não no código:
- Lista de `category` (vai expandir conforme aparecem novos modos de falha)
- Prompt do judge (pré e pós) — vai ser recalibrado depois dos primeiros vídeos
- Mapping de severidade → comportamento (mesmo que hoje seja "tudo bloqueia")
- Modelo escolhido pra pós-gate (multimodal: Gemini 2.5 / Claude / GPT-4o)

Esse princípio se aplica **a todo o projeto**, não só ao policy check.
Ver bullet "Config isolada" em §4.

---

## 8. Upload YouTube

### 8.1 Stack escolhida

| Item | Decisão | Autoria |
|---|---|---|
| API | YouTube Data API v3 | 🤖→👤 (única oficial) |
| Endpoint upload | `videos.insert` (resumable) | 🤖→👤 |
| Endpoint miniatura | `thumbnails.set` | 🤖→👤 |
| Auth | OAuth 2.0 desktop flow + refresh token persistido em `.secrets/youtube_token.json` | 🤖→👤 |
| SDK | `google-api-python-client` + `google-auth-oauthlib` | 🤖→👤 (padrão Google) |

**Por quê desktop OAuth:** YouTube **não aceita service account** pra upload
(documentado). Desktop flow gera refresh token de uso eterno, salva em arquivo
local — você autoriza 1 vez, código nunca mais pede login.

### 8.2 Política de privacidade do upload (escada)

🤖→👤 **Decidido: `unlisted` no upload, promove pra `public` manual depois.**

| `publish_mode` (config) | Comportamento |
|---|---|
| `unlisted_review` (default) | Sobe `unlisted`, CLI mostra link, você abre, assiste, promove no Studio |
| `direct_public` | Sobe `public` direto. **Habilitar só depois de ~20 vídeos** com pós-gate calibrado |
| `private_only` | Sobe `private`. Útil quando o projeto API ainda não passou auditoria do Google |

**Por quê:** o pós-gate ainda não foi calibrado (LLM-as-judge é ruidoso nos
primeiros 5–10 vídeos). Camada humana extra de 2min/vídeo é seguro barato.
Migração entre modos é só trocar 1 linha de config — princípio de §4.

**Restrição técnica:** projetos novos da API começam em modo "unverified" e
**forçam** `private` em qualquer upload, ignorando `privacyStatus`. Pra usar
`unlisted`/`public` é preciso submeter o projeto a **auditoria de compliance**
do Google. Ver §8.6.

### 8.3 Metadata do upload (título, descrição, tags)

🤖→👤 **Decidido: template + slot filling, com `sinopse_curta` adicionada ao roteiro JSON.**

| Campo | Origem |
|---|---|
| Título | `roteiro.titulo` + sufixo de canal definido em `config/youtube.yaml` (ex.: `"{titulo} \| contadinhos"` — lowercase) |
| Descrição | Template fixo em `config/youtube.yaml`: `{titulo}\n\n{sinopse_curta}\n\n{boilerplate_canal}` |
| Tags | Lista fixa de 8–12 tags em config + 1–2 específicas extraídas do roteiro |
| `categoryId` | `22` (People & Blogs) ou `1` (Film & Animation) — 🤖 vai de **`1`** (animação combina mais com aquarela) |
| `defaultLanguage` | `pt-BR` |
| `defaultAudioLanguage` | `pt-BR` |

**Por quê template em vez de LLM:**
- Identidade de tom estável entre vídeos (LLM oscila).
- Descrição em canal kids é dominantemente boilerplate; LLM aqui só gera ruído.
- Tags pesam pouco em "made for kids" (algoritmo prioriza engagement + flag).
- Sem pressão de métrica/discovery (§1) → otimizar discovery não é objetivo.

**Mudança no schema do roteiro:** adicionar campo `sinopse_curta` (1–2 frases)
no JSON do LLM roteirista. Custo marginal zero (LLM já tem o roteiro inteiro).

### 8.4 `selfDeclaredMadeForKids`

🤖→👤 **Decidido: sempre `true`.**

Sem exceção. Vai como `status.selfDeclaredMadeForKids: true` em todo upload.
Aceita as restrições COPPA implícitas:
- Sem comentários
- Sem notificações
- Sem ads personalizadas
- Sem playlists "Watch Later" pelos espectadores
- Sem cards/end screens em alguns formatos

Tudo já aceito em §1.

### 8.5 Miniatura customizada

🤖→👤 **Decidido: `thumbnails.set` com a imagem-chave do protagonista. Canal já verificado por SMS em 2026-05-04 ✅ — falta só auditoria do projeto API pra liberar.**

**Restrição técnica:** custom thumbnails exigem **canal verificado por SMS**
(além da auditoria do projeto API). Se o canal não tá verificado, `thumbnails.set`
falha — fallback é deixar YouTube auto-extrair frame.

**Lógica do código:**
```
if canal_verificado and projeto_api_auditado:
    upload_thumbnail(imagem_chave_protagonista)
else:
    log warning, segue sem thumbnail custom
```

Imagem-chave do protagonista já é gerada no pipeline (§3) — reaproveitamento
direto. Crop/resize pra 1280×720 JPG/PNG (≤2MB) feito via Pillow.

### 8.6 Auditoria do projeto API + verificação do canal

🤖→👤 **Decidido: começar em modo "private only" e aplicar à auditoria + verificação na primeira semana.**

Sequência (estado em 2026-05-04):
1. ✅ Criar canal YouTube `@contadinhos`.
2. ✅ Verificar canal por SMS no Studio (pré-req pra `thumbnails.set`).
3. ⏳ Criar projeto Google Cloud, ativar **YouTube Data API v3** (Vertex AI já está ativa pelo crédito Veo).
4. ⏳ Configurar **OAuth desktop client** no Google Cloud Console → baixar `client_secret.json` → salvar em `.secrets/`.
5. ⏳ Rodar fluxo OAuth uma vez, gerar refresh token, salvar em `.secrets/youtube_token.json`.
6. **Fase 7 do MVP:** upload primeiros 1–2 vídeos como `private` (forçado pelo unverified-project). Servem pra validar pipeline ponta-a-ponta.
7. **Pós Fase 7:** submeter [formulário de auditoria de compliance](https://support.google.com/youtube/contact/yt_api_form) do Google. Pode demorar dias.
8. **Pós-auditoria:** trocar `publish_mode` em config pra `unlisted_review` (default).

**Por quê esperar:** auditoria não é instantânea, mas pipeline de geração é
muito mais demorado pra construir. Logo, o gate da auditoria não bloqueia
desenvolvimento — quando o pipeline tiver vídeo pra subir, a auditoria já
passou (ou tá perto).

### 8.7 Quota

Default Google: **10.000 unidades/dia**. Custos relevantes:

| Operação | Unidades |
|---|---|
| `videos.insert` | 1.600 |
| `thumbnails.set` | 50 |
| `videos.update` (mexer descrição depois) | 50 |
| `videos.list` (consulta) | 1 |

**Custo por vídeo publicado:** ~1.700 unidades. Limite de **~5 vídeos/dia**
no quota default — folga absurda pra ritmo on-demand.

🤖→👤 **Decidido: não pedir aumento de quota agora.** Reabrir só se ultrapassar
3 vídeos/dia regulares.

---

## 8.8 Tratamento de erros e retries em providers

🤖→👤 **Decidido (sessão 2026-05-07):** padrão único pra todos os
providers (Veo, Kling, Nano Banana, ElevenLabs, Whisper, LLM roteirista,
LLM auditor, YouTube). Vive em `core/providers/retry.py` e é aplicado
via decorator nas chamadas externas.

| Item | Decisão |
|---|---|
| Política | Exponential backoff: tentativas em 1s, 4s, 16s; **3 tentativas no total** |
| Quando re-tentar | **Só** em `5xx`, timeout, e exceções de rede (`httpx.ConnectError`, `httpx.ReadTimeout`) |
| Quando **não** re-tentar | `4xx` (auth, validation, quota, permission) — falha imediata. **Pré/pós-gate `review_required`** (§7.3) — não é erro, é decisão humana. |
| Exceção final | `ProviderError(provider, attempt, original)` — typed, capturada por CLI/bot pra mensagem clara |
| Custo da tentativa que falhou | **Registrar no ledger mesmo assim** (`step: "video", attempt: 2, cost_usd: 0, paid_via: "free_failed"` ou `"google_credits"` se a API cobrou). Razão: providers podem cobrar parcial em jobs longos que falham (Veo já cobrou inferência mesmo se polling der timeout). |
| Configurabilidade | `config/providers.yaml::retry.{max_attempts, base_delay_s, retryable_status}` — overridable por provider |
| Jitter | `±25% aleatório` no delay pra evitar thundering herd em rerun manual |

**Por quê assim:**
- 3 tentativas é teto pragmático: cobre flakey transitório (~95% dos casos), evita "loop infinito" que esconde problema real.
- Não retentar 4xx evita queima de quota em problema sistemático (auth quebrada → 100 tentativas em 1min).
- Registrar custo de attempt falhada bate com princípio de §11.2: ledger é a verdade, mesmo dor.
- Decorator vs middleware: decorator é mais navegável pra agente IA — vê na própria função quem retenta. Middleware obscurece.

**Por quê não retry em policy_check:**
Já decidido em §7.3 ("sem auto-retry") — humano sempre decide. Decorator
de retry **explicitamente exclui** as funções de gate.

---

## 9. Orquestração

### 9.1 Pipeline core (headless) ↔ Frontends (camada de interação)

👤 **Decidido: pipeline core é uma biblioteca Python sem UI; frontends são módulos finos que chamam o core. Múltiplos frontends coexistem.**

Conceito:

```
        ┌──────────────────────────────────────────────────┐
        │ Pipeline core (src/contadinhos/core/)            │
        │                                                  │
        │  transcribe / script / images / video / tts /    │
        │  assemble / policy / upload / budget             │
        │                                                  │
        │  • Funções puras sobre stories/<id>/             │
        │  • Sem print, sem prompt, sem rede de UI         │
        │  • Retorna estado da Story (campo "next_action") │
        └──────────────────────────────────────────────────┘
                  ▲                              ▲
                  │                              │
   ┌──────────────┴──────────────┐  ┌────────────┴─────────────┐
   │ Frontend CLI                │  │ Frontend Telegram        │
   │ (src/contadinhos/frontends/ │  │ (src/contadinhos/        │
   │  cli/)                      │  │  frontends/telegram/)    │
   │                             │  │                          │
   │  • typer subcommands        │  │  • python-telegram-bot   │
   │  • terminal prompts         │  │  • inline keyboards      │
   │  • dev/debug primário       │  │  • UX "set and forget"   │
   └─────────────────────────────┘  └──────────────────────────┘
```

**Princípio crítico:** o core **nunca** importa frontends. Frontends importam o
core. Trocar/adicionar frontend = adicionar módulo, não mexer no pipeline.

**Por quê separar:**
- Você quer **Telegram pra deixar rodando** (mandar áudio do celular, fazer curadoria de qualquer lugar). Mas é uma decisão de UX — o pipeline em si independe.
- Em desenvolvimento/debug, **CLI é mais rápido** — você roda `contadinhos script ...`, vê o JSON, edita YAML, repete. Em Telegram seria penoso.
- Coexistência de frontends é o **mesmo padrão** que `VideoGenerator` (Kling/Veo/Runway) e `TTSProvider` (ElevenLabs/...). Você já comprou esse princípio em §4: provider-agnostic. Aqui é frontend-agnostic.
- Futuro: web UI / Discord / WhatsApp / agente Claude — todos plugam no mesmo core.

### 9.2 Frontend CLI (dev primário)

🤖→👤 **Decidido: typer com subcomandos discretos. Operação sobre `stories/<id>/`. Resumível.**

```
$ contadinhos new "raposa-curiosa"
  → cria stories/2026-05-04-raposa-curiosa/ com estrutura padrão

$ contadinhos transcribe stories/2026-05-04-raposa-curiosa/
  → audio.m4a → transcript.txt (Whisper)

$ contadinhos script stories/2026-05-04-raposa-curiosa/
  → LLM roteirista, gera roteiro.json + dispara pré-gate
  → se review_required, CLI imprime flags + abre $EDITOR pra editar roteiro

$ contadinhos images stories/2026-05-04-raposa-curiosa/
  → gera 4 candidatas por imagem-chave; CLI mostra paths e pede escolha

$ contadinhos video stories/2026-05-04-raposa-curiosa/
  → gera clipes I2V/T2V via Veo (default)

$ contadinhos tts stories/2026-05-04-raposa-curiosa/
  → ElevenLabs por cena

$ contadinhos assemble stories/2026-05-04-raposa-curiosa/
  → FFmpeg: concat + drawtext + mix → final.mp4 → dispara pós-gate

$ contadinhos publish stories/2026-05-04-raposa-curiosa/
  → upload YouTube no publish_mode configurado

$ contadinhos run stories/2026-05-04-raposa-curiosa/
  → atalho: roda todas as etapas, para em cada gate humano

$ contadinhos status stories/2026-05-04-raposa-curiosa/
  → imprime "next_action" (qual etapa rodar a seguir, ou qual decisão pendente)
```

### 9.3 Frontend Telegram (operação)

🤖→👤 **Decidido: bot Telegram em modo polling, primeiro frontend "always-on". Ver §9.4 pra design detalhado.**

Motivação textual sua: *"posso mandar o audio e fazer curadoria por la, acho que fica facil de deixar rodando"*. Bot transforma o iPhone na interface — você grava história, manda áudio, recebe pings de curadoria onde estiver.

### 9.4 Design do bot Telegram

🤖→👤 **Decidido:**

| Item | Decisão |
|---|---|
| Lib | `python-telegram-bot` ≥21 (async, mature). Pin pra última versão estável no `pyproject.toml`. |
| Ambiente Python | venv padrão (compatível com `uv venv` ou `python -m venv`). |
| Modo | **Polling** (não webhook). Mais simples; sem necessidade de TLS/host público. |
| Hosting **inicial** | Local macOS via `launchctl` (gratuito). Mac precisa estar acordado — `caffeinate -dims` no plist ou desligar sleep do disco. |
| Hosting **plano** | Migrar pra **VPS dedicado** quando o pipeline estabilizar (DigitalOcean/Hetzner/Linode US$5–10/mês, polling continua, Mac fica fora do caminho). Decisão registrada em §15 pra reabrir. |
| Auth | Allowlist de `chat_id` em `config/telegram.yaml`. Mensagem de qualquer outro chat = ignorada com log. |
| Storage | Mesmo `stories/<id>/` que CLI. Bot só cria/lê arquivos lá. |
| Concurrency | **Single-story queue.** Bot processa 1 story por vez; novas mensagens com áudio durante processamento → resposta imediata `"⏳ ocupado processando '<id-atual>'. Sua mensagem entrou na fila (posição N)."`. **Sem worker pool, sem complexidade de paralelismo.** |
| Interrupção | Toda mensagem de "estou trabalhando" carrega botão **❌ Cancelar story atual**. Cancelamento aborta polling/wait local e libera a fila. **Quirk: jobs externos (Veo, Kling) podem continuar rodando server-side e custar mesmo após cancel** — bot avisa isso na confirmação. |

**Fluxo conversacional:**

1. Você manda **áudio** (voice message ou m4a) no chat com o bot.
2. Bot cria `stories/<YYYY-MM-DD>-<n>/` com `audio.m4a`. Responde: *"Áudio recebido. Quer um slug específico ou gero do roteiro?"*. Você responde (texto livre ou botão "auto").
3. Bot dispara `transcribe` + `script` em background. Responde com **roteiro JSON pretty + sinopse + policy_check** + botões inline:
   - ✅ Aprovar
   - ✏️ Pedir nova versão (você manda comentário)
   - ❌ Abandonar
4. Aprovado → bot dispara `images`. Por imagem-chave, manda **media group de 4 fotos** + botões `1` `2` `3` `4` `🔄 Regerar`.
5. Imagens escolhidas → bot dispara `video` (Veo, ~25-40min total). Responde: *"Gerando vídeo. Te aviso em ~30min."*. Reporta progresso a cada N cenas.
6. Vídeo pronto → bot dispara `tts` + `assemble` + pós-gate. Manda **`final.mp4`** (≤50MB OK) + flags do pós-gate + botões:
   - 🚀 Subir pra YouTube (unlisted)
   - ❌ Abandonar
   - 🎬 Regerar cena específica (abre menu com índices)
7. Upload feito → bot manda link do YouTube + botão **"Promover pra public"** (chama `videos.update` com `privacyStatus=public`).

**Quirks técnicos:**
- Telegram bot file limit: **50MB**. 75s @ 1080p H.264 fica em 10–25MB tipicamente. Se passar, bot manda thumbnail + path local + sobe pro YouTube direto.
- Mensagens longas (roteiro JSON de 50 linhas): Telegram corta em 4096 chars. Bot quebra em múltiplas mensagens ou manda como arquivo `.json`.
- Polling local em macOS: `launchctl` com `KeepAlive=true`. Bot se auto-restart se morrer.
- Mac dormindo = bot offline. Mitigação inicial: ajuste de Energy Saver pra "Prevent computer from sleeping when display is off" + sem sleep de disco. Mitigação definitiva: VPS (ver §15).
- Cancelamento de Veo/Kling: a Vertex AI `operations` API expõe `operations.cancel`, mas pode não interromper geração já em curso (server billing pode persistir). Documentar UX claramente: "cancel aborta espera local; cobrança server-side pode prosseguir".

### 9.5 Por quê on-demand (e não scheduler/agente)

🤖→👤

- **Você falou explicitamente:** ritmo é on-demand; conta ~1 história/dia, mas nem toda vira vídeo.
- **Scheduler (cron/job)** seria over-engineering — nunca vai rodar sozinho.
- **Agente custom** (LLM orquestrando): violenta o princípio. Cada etapa tem decisão humana embutida (escolha de imagens, gates de policy). LLM no leme não traz benefício, só intermedia mensagens.
- **CLI + Telegram** dão resumibilidade: parar no meio, retomar amanhã, em qualquer ponto.

### 9.6 Estado no filesystem

Estrutura padrão de `stories/<id>/`:

```
stories/2026-05-04-raposa-curiosa/
├── audio.m4a               # input cru
├── transcript.txt          # output Whisper
├── roteiro.json            # output LLM roteirista (inclui policy_check)
├── images/
│   ├── raposa/
│   │   ├── candidate_0.png
│   │   ├── candidate_1.png
│   │   ├── candidate_2.png
│   │   ├── candidate_3.png
│   │   └── chosen.png      # symlink ou cópia da escolhida
│   └── menininha/...
├── clips/
│   ├── scene_01.mp4
│   ├── scene_02.mp4
│   └── ...
├── audio/
│   ├── narration_01.wav
│   └── ...
├── final.mp4
├── policy_check_post.json  # output do pós-gate
└── upload_result.json      # videoId, URL, status
```

**Por quê filesystem-as-state:** zero infra (sem DB, sem queue), debugável
trivialmente (você abre o diretório), versionável seletivamente
(`.gitignore` blob assets, mantém JSONs). **Bônus para multi-frontend:** CLI e
Telegram compartilham estado sem precisar inventar mecanismo de sync.

### 9.7 Concorrência CLI ↔ Telegram (file lock por story)

🤖→👤 **Decidido (sessão 2026-05-07):** filesystem-as-state (§9.6) +
múltiplos frontends (§9.1) abrem porta pra race condition: você roda
`contadinhos images` no terminal e o bot Telegram, em paralelo, dispara
a mesma etapa pelo iPhone. Resultado: dois processos escrevendo no
mesmo `stories/<id>/`.

**Solução:** **lock advisory de filesystem** por story.

| Item | Decisão |
|---|---|
| Mecanismo | `fcntl.flock` (Linux/macOS) sobre `stories/<id>/.lock` |
| Aquisição | Cada subcomando do CLI e cada handler do bot que muta arquivos da story adquire lock no início, libera no fim |
| Comportamento se lock tomado | CLI: `exit 1` com mensagem `"story <id> em uso por outro processo (PID X)"`. Bot: responde `"⏳ outro processo está mexendo nessa story"` e aborta sem entrar na fila. |
| Limpeza | Lock é liberado pelo kernel ao morte do processo (kill, crash) — sem stale locks |
| Reentrância | Não. Mesmo processo não chama duas etapas em paralelo no projeto. |
| Onde mora | `core/story.py::Story.__enter__/__exit__` — context manager. Etapas usam `with story.lock(): ...` |

**Por quê não fila distribuída / lockfile com PID / mutex em arquivo SQLite:**
- `flock` é POSIX, zero deps, zero infra.
- `.lock` no próprio dir da story = escopo natural (uma story = uma unidade de trabalho).
- Locking entre stories é desnecessário (cada story tem dir próprio).
- Bot já tem single-story queue interno (§9.4); o lock só protege contra **CLI + bot simultâneos** (humano duplo-comando).

**Implicação pro código:** `core/story.py::Story` ganha context manager.
Toda etapa do core que muta a story usa `with story.lock(): ...`. Lock
fica em `stories/<id>/.lock` (gitignored junto com o resto).

### 9.8 Colisão de nome de story

🤖→👤 **Decidido (sessão 2026-05-07):** se `stories/<YYYY-MM-DD>-<slug>/`
já existir, `Story.create()` **adiciona sufixo numérico** (`-2`, `-3`...).
Não sobrescreve, não pergunta, não falha. Justificativa: você grava
duas histórias da raposa no mesmo dia — caso real, esperado.

### 9.9 Frequência

🤖 **Decidido: livre, on-demand. Sem mínimo, sem máximo enforçado pelo código.**
Teto de **custo** controla — ver §11.

---

## 10. Identidade do canal

### 10.1 Nome e marca

🤖→👤 **Cravado em 2026-05-04:**

| Item | Valor | Estado |
|---|---|---|
| Nome do canal | **contadinhos** (lowercase) | ✅ Configurado no YouTube Studio |
| Handle | **@contadinhos** | ✅ Reservado — `youtube.com/@contadinhos` |
| Tagline / descrição do canal | **"Histórias em aquarela para crianças"** + boilerplate de §10.4 | ✅ Inserida no Studio |
| Bot Telegram | **@contadinhosBot** (handle lowercase `contadinhosbot`) | ✅ Criado no BotFather |

**Convenção de capitalização:** o canal usa **lowercase** ("contadinhos") como
exibido no Studio. Por consistência de marca, todo lugar que referencia o canal
em texto/descrição/título usa a mesma forma — **lowercase**. Inclui o sufixo
do título dos vídeos: `{titulo} | contadinhos`.

### 10.2 Vinheta de abertura e fechamento

🤖 **Decidido:**

| Item | Decisão |
|---|---|
| Vinheta abertura | **2 segundos**, estática ou animação simples (logo do canal + tagline aparecendo). Áudio: jingle curto (TTS ou trecho de música da YT Audio Library). Gerada **uma vez**, reaproveitada em todo vídeo. |
| Vinheta fechamento | **3 segundos**, estática (logo + "fim" ou "até logo"). Mesma origem da abertura. |
| Geração inicial | 🤖→👤 **Nano Banana** (Gemini 2.5 Flash Image, `gemini-2.5-flash-image`) com prompt de identidade + Pillow pra ajuste de texto. **Não gera no pipeline** — é asset estático em `assets/intro.mp4` e `assets/outro.mp4`. **Por quê Nano Banana:** acurácia visual + renderização de texto na imagem (logo + tagline) é ponto forte do modelo; resolve a vinheta em uma chamada. |

**Por quê asset estático:** vinheta nunca muda. Gerar a cada vídeo seria
desperdício; um glitch de IA na vinheta arranha a marca em todos os vídeos.

### 10.3 Naming convention dos arquivos

🤖→👤 **Decidido:**

| Item | Padrão |
|---|---|
| Story ID (interno) | `<YYYY-MM-DD>-<slug>` (ex.: `2026-05-04-raposa-curiosa`) |
| Título YouTube | `{roteiro.titulo} \| contadinhos` (lowercase, configurável em `youtube.yaml`) |
| Slug | minúsculo, hífen, ascii; gerado do título via `python-slugify` (`max_length=40`, `word_boundary=True`). 🤖→👤 (2026-05-07): sem lista própria de stopwords — `slugify` já corta acentos e pontuação; "sem stopwords" da v1 era complexidade desnecessária. Em colisão, sufixo numérico (§9.8). |

### 10.4 Descrição padrão do canal (boilerplate)

🤖→👤 **Decidido (template em `config/youtube.yaml`):**

```
{titulo}

{sinopse_curta}

🎨 Histórias em aquarela para crianças.
🎙️ Narração suave para os pequenos.
👶 Conteúdo feito para crianças.

📺 Inscreva-se: youtube.com/@contadinhos

#historiainfantil #aquarela #criancas
```

Hashtags inclusas porque YouTube Kids reconhece e categoriza por elas
(mesmo sem ranqueamento pra adultos).

---

## 11. Frequência + teto de custo

### 11.1 Cadência alvo

🤖→👤 **Decidido: começar em ~2 vídeos/semana, escalar conforme calibrar.**

| Fase | Cadência alvo | Por quê |
|---|---|---|
| Calibração (mês 1–2) | 1–2 vídeos/semana | Aprender o pipeline, calibrar pós-gate, ajustar prompts. Volume baixo prioriza qualidade. |
| Regime (mês 3+) | 2–3 vídeos/semana (~10/mês) | Cadência sustentável pra canal sem pressão de algoritmo. Histórias contadas ≠ histórias gravadas ≠ vídeos publicados; funil natural. |
| Pico (eventualmente) | até 5/semana | Só com pipeline estável e custo monitorado. |

**Por quê não "quase diário"/30 vídeos:** a estimativa original em §6 considerou
30/mês como teto. Realidade é mais conservadora — você conta ~1/dia, mas:
- Nem toda história vale virar vídeo.
- Gravação só rola em parte das noites (filha já dormiu, contexto, qualidade do áudio).
- Revisão humana de 30s/imagem + 2–5min roteiro + 2min upload = **~10–15 min de atenção real por vídeo**, mesmo com pipeline rodando sozinho. Diário viraria "trabalho".

### 11.2 Teto de custo (com tracking dual nominal vs out-of-pocket)

🤖→👤 **Decidido (Opção A):** crédito Google é tratado separado do bolso.
Ledger registra **valor nominal** sempre; teto mensal mede **só out-of-pocket**.

| Item | Valor inicial | Aplica a | Onde mora |
|---|---|---|---|
| Teto **por vídeo** | **US$30** (Kling) / **US$80** (Veo) — calibração; abaixa pra US$25/US$60 após 5–10 vídeos reais (ver §19) | **valor nominal** — catch runaway mesmo em crédito | `config/budget.yaml` |
| Teto **mensal total** | **US$150/mês** | **out-of-pocket apenas** — crédito Google não conta | `config/budget.yaml` |
| **Pre-flight check** (antes de chamar Veo/Kling) | Estima `len(cenas) × duracao_média × $custo_por_s` e **aborta antes de gastar** se passar do teto. Evita queima a posteriori. | nominal | `core/video/factory.py` (lê `config/providers.yaml::costs_per_second`) |
| Alerta de teto por-vídeo (post-hoc) | Hard fail no CLI se ledger somar acima do teto após etapa concluída — fallback caso pre-flight tenha errado a estimativa | nominal | Código consulta config |
| Alerta de teto mensal | Soft warning aos 80% out-of-pocket (~US$120), hard block aos 100% | out-of-pocket | Code lê ledger |
| Display no CLI antes de cada vídeo | `"out-of-pocket: US$X / US$150 | nominal estimado: US$Y / teto US$Z"` | — | — |

**Por quê dual:**
- Nominal mostra o "custo real" do vídeo independente de quem paga — calibra
  expectativa pro pós-crédito.
- Out-of-pocket é o que dói no cartão — só ele dispara o teto mensal.
- Quando o crédito esgotar, **toda linha vira out-of-pocket** automaticamente
  e o teto começa a morder.

**Por quê teto inicial mais largo + pre-flight** (decisão revisada em 2026-05-06):
- Estimativa de §6 é "ordem de grandeza"; primeiros vídeos reais são o teste
  de fogo. Teto colado na ponta alta da estimativa (US$60 vs US$30–55) tem
  ~9% de folga — qualquer surpresa vira hard fail desnecessário.
- Pre-flight check elimina a queima a posteriori: se o vídeo "vai custar
  US$70" estimado pela contagem de cenas, aborta antes de chamar Veo, em
  vez de descobrir só após gastar.
- Teto US$80 inicial dá margem honesta na calibração; após 5–10 vídeos
  reais, abaixa pra US$60 (ou outro número informado pelos dados) —
  registrado em §19 como ponto de re-decisão.

### 11.3 Ledger de custo

🤖→👤 **Decidido:** cada vídeo grava `cost_ledger.json` em `stories/<id>/` com
campo `paid_via` por item para distinguir crédito Google de out-of-pocket:

```json
{
  "story_id": "2026-05-04-raposa-curiosa",
  "items": [
    { "step": "transcribe",  "provider": "openai-whisper",       "cost_usd": 0.006, "paid_via": "out_of_pocket" },
    { "step": "script",      "provider": "claude-opus-4.7",      "cost_usd": 0.04,  "paid_via": "out_of_pocket" },
    { "step": "images",      "provider": "nano-banana",          "cost_usd": 0.18,  "paid_via": "google_credits", "qty": 12 },
    { "step": "video",       "provider": "veo-3.1",              "cost_usd": 37.50, "paid_via": "google_credits", "qty": 10 },
    { "step": "tts",         "provider": "elevenlabs",           "cost_usd": 0.22,  "paid_via": "out_of_pocket" },
    { "step": "policy_post", "provider": "gemini-2.5-flash",     "cost_usd": 0.08,  "paid_via": "google_credits" }
  ],
  "total_usd_nominal": 38.03,
  "total_usd_out_of_pocket": 0.27,
  "exceeded_per_video_cap": false
}
```

**Valores válidos de `paid_via`:**
- `out_of_pocket` — saiu do cartão (OpenAI, Anthropic, ElevenLabs, Kling, Runway)
- `google_credits` — Veo, Nano Banana, Gemini-as-judge enquanto durar o crédito.
  Quando o crédito esgotar, mudar default em `config/providers.yaml` automaticamente
  (ou só remarcar manualmente nos novos ledgers).

**Comportamento do CLI:**
- Antes de cada etapa cara: mostra estimativa e custo acumulado out-of-pocket
  do mês (`"este mês: US$84 de US$150 out-of-pocket"`).
- Antes de cada vídeo: mostra estimativa nominal e dispara hard fail se passar
  do teto por-vídeo (US$25/US$60).
- Antes de upload: mostra resumo final (`"este vídeo: US$38 nominal, US$0,27 out-of-pocket"`).

Soma dos `total_usd_out_of_pocket` do mês = custo mensal real. Soma dos
`total_usd_nominal` do mês = custo "se fosse pago" (informativo, calibra
expectativa pro pós-crédito).

### 11.4 Comparativo Kling vs Veo

| Custo/vídeo | Veo 3.1 | Kling 2.0 |
|---|---|---|
| 75s típico | ~US$30–55 (≈$0,50/s @ 1080p) | ~US$10–18 |
| **10 vídeos/mês** | US$300–550 | US$100–180 |
| **Posição atual** | 🤖→👤 **Default inicial** — Kaique tem créditos Google ativos | Alternativa econômica quando o crédito Google esgotar |

🤖→👤 **Decidido: Veo 3.1 padrão inicial enquanto houver créditos Google.**
Kling 2.0 fica plugável via `VideoGenerator` — basta swap em
`config/providers.yaml`. Quando o crédito esgotar, reavaliar com base em (a)
qualidade real observada nos primeiros vídeos, (b) custo mensal sustentável.

**Importante:** o **teto de custo** em §11.2 mede saída de bolso. Enquanto
créditos Google bancam o Veo, custo "real" é ~zero pra geração de vídeo, mas o
ledger ainda registra **valor nominal** pra calibrar o orçamento futuro.

### 11.5 Reaproveitamento da pasta `veo3/`

A pasta `veo3/` já existente no repo (gerador Veo do projeto raupplandscape)
contém código funcional pra Veo 3.1 via Vertex AI:
- ~~ADC com `gcloud auth application-default login`~~ — **substituído** (sessão
  2026-05-07) por API key (`GOOGLE_GENERATIVE_AI_API_KEY`). `genai.Client(api_key=key)`
  em vez de `genai.Client(vertexai=True)`. Crédito Google fica associado à key.
- Polling de operação (timeout 600s) — reaproveita
- ~~Chaining last-frame → first-frame da próxima cena~~ — **não vai ser
  reaproveitado por padrão** (§3.2). Código de extract-last-frame fica como
  utilitário caso o flag opt-in seja habilitado depois.
- Concat e recode com ffmpeg — reaproveita
- Negative prompt list — reaproveita (mover pra `config/providers.yaml`)

🤖 **Decidido: portar `veo3/generate.py` pra `src/contadinhos/core/video/veo.py`** na
Fase 4 (§13). Pasta `veo3/` fica como referência até a porta ser concluída;
depois move pra `docs/reference/veo3-original.py` ou apaga. Continua **gitignored**
até decisão final.

---

## 12. Estrutura do repo

🤖 **Decidido: layout Python `src/` padrão, módulos por etapa do pipeline, configs externas, secrets isolados.**

```
contadinhos/
├── README.md
├── CONTEXT.md                      # glossário de domínio (já existe)
├── pyproject.toml                  # deps via uv ou poetry
├── .env.example                    # template de secrets
├── .gitignore
├── docs/
│   ├── decisions.md                # este arquivo
│   └── adr/                        # ADRs futuros (vazio por enquanto)
├── config/
│   ├── pipeline.yaml               # target_duration_s, durações por cena, ...
│   ├── style.yaml                  # string de estilo aquarela, prompts base
│   ├── policy.yaml                 # categorias do gate, prompts do judge
│   ├── youtube.yaml                # template descrição, tags fixas, naming
│   ├── budget.yaml                 # tetos de custo
│   ├── voices.yaml                 # ElevenLabs voice IDs por personagem
│   └── providers.yaml              # provider defaults (kling, imagen-3, ...)
├── assets/
│   ├── intro.mp4                   # vinheta abertura (estático)
│   ├── outro.mp4                   # vinheta fechamento (estático)
│   ├── music/                      # YT Audio Library curada (5–10 faixas)
│   └── fonts/                      # fonte da legenda
├── stories/                        # WORKING DIR (no git, gitignored)
│   └── 2026-05-04-raposa-curiosa/
│       ├── audio.m4a
│       ├── transcript.txt
│       ├── roteiro.json
│       ├── images/
│       ├── clips/
│       ├── audio/
│       ├── final.mp4
│       ├── policy_check_post.json
│       ├── cost_ledger.json
│       └── upload_result.json
├── .secrets/                       # gitignored
│   └── youtube_token.json          # OAuth refresh token
├── veo3/                            # 🤖 referência temporária — gitignored
│   └── ...                          # gerador Veo 3.1 do raupplandscape
│                                    # Será portado em Fase 4 (§13).
├── src/
│   └── contadinhos/
│       ├── __init__.py
│       ├── core/                    # 🤖→👤 PIPELINE HEADLESS — sem UI
│       │   ├── __init__.py
│       │   ├── config.py            # loader único pra configs YAML
│       │   ├── story.py             # struct + IO sobre stories/<id>/
│       │   ├── schemas.py           # pydantic do roteiro, policy_check
│       │   ├── transcribe.py        # Whisper
│       │   ├── script/
│       │   │   ├── __init__.py
│       │   │   ├── prompts.py       # prompt do roteirista (carrega config)
│       │   │   └── llm.py           # chamada LLM
│       │   ├── images/
│       │   │   ├── __init__.py
│       │   │   ├── base.py          # interface ImageGenerator
│       │   │   ├── imagen.py        # impl Imagen 3
│       │   │   └── midjourney.py
│       │   ├── video/
│       │   │   ├── __init__.py
│       │   │   ├── base.py          # interface VideoGenerator
│       │   │   ├── veo.py           # 🤖→👤 default — porte de veo3/
│       │   │   ├── kling.py         # alternativa econômica
│       │   │   └── runway.py
│       │   ├── tts/
│       │   │   ├── __init__.py
│       │   │   ├── base.py          # interface TTSProvider
│       │   │   └── elevenlabs.py
│       │   ├── assemble/
│       │   │   ├── __init__.py
│       │   │   └── ffmpeg.py        # concat, mix, drawtext, music
│       │   ├── policy/
│       │   │   ├── __init__.py
│       │   │   ├── pre_gate.py
│       │   │   └── post_gate.py
│       │   ├── upload/
│       │   │   ├── __init__.py
│       │   │   ├── youtube.py
│       │   │   └── auth.py
│       │   ├── budget.py            # ledger, alerts
│       │   └── utils/
│       └── frontends/               # 🤖→👤 CAMADA DE INTERAÇÃO
│           ├── __init__.py
│           ├── cli/
│           │   ├── __init__.py
│           │   └── main.py          # typer subcommands → core
│           └── telegram/
│               ├── __init__.py
│               ├── bot.py           # entrypoint polling
│               ├── handlers.py      # message/callback handlers
│               ├── keyboards.py     # inline keyboard factories
│               └── flow.py          # wizard de curadoria por story
└── tests/
    ├── unit/
    └── integration/
```

### 12.1 Convenções

🤖→👤 **Decidido:**

| Item | Convenção |
|---|---|
| Linguagem | Python `>=3.12,<3.14` (pin em `pyproject.toml::requires-python`). 🤖→👤 (2026-05-07): aceita 3.13 quando estável; bloqueia 3.14+ até validar deps. |
| `uv.lock` | Commitado no git (padrão `uv`). Garante reproducibilidade de venv entre máquinas/restore. 🤖→👤 (2026-05-07). |
| Tipos | `pydantic` v2 pra schemas (roteiro, policy_check, etc.) |
| Lint/format | `ruff` |
| Tests | `pytest` |
| Deps | `uv` (rápido, lock determinístico; cria venv padrão `.venv/`) |
| CLI | `typer` (decorators, type-hint-based) |
| Telegram bot | `python-telegram-bot` ≥21 (latest stable, async) |
| Configs | YAML carregado por `pydantic-settings` |
| Secrets | `.env` + `python-dotenv` |
| FFmpeg | `subprocess` direto (mais transparente que `ffmpeg-python`) |
| HTTP | `httpx` (já vem como sub-dep de `google-genai`) |
| Google APIs | `google-genai` (Veo + Nano Banana) + `google-api-python-client` + `google-auth-oauthlib` (YouTube) |
| Persistência | **Filesystem** (`stories/<id>/` + `cost_ledger.json` por story). Sem DB por enquanto. Supabase reservado em §15 para quando aparecer caso de uso real (Web UI, analytics cross-story). |

### 12.2 Princípios

- **Pipeline core nunca importa frontends.** Frontends importam o core. Mesmo padrão que o code já trata `VideoGenerator` ↔ provedores: o produtor não conhece o consumidor.
- **Cada provider é um módulo** com interface comum (`base.py`). Trocar provider = trocar import + linha de config.
- **Cada frontend é independente.** Adicionar Discord/Web/Slack = novo módulo em `frontends/`, zero alteração no core.
- **Funções puras sobre o roteiro JSON.** Etapa lê JSON + arquivos do `stories/<id>/`, escreve novos arquivos. Nada de estado em memória entre comandos.
- **Configs nunca importadas como código.** Sempre carregadas em runtime via `core.config.load("policy")`.
- **Secrets nunca em config versionado.** Só em `.env` (gitignored).
- **CLI = dev primário.** Use `frontends/cli` quando estiver iterando em código. Telegram é UX de operação, não de desenvolvimento.

---

## 13. Fases de implementação (MVP sequencial)

🤖→👤 **Decidido: 10 fases. Cada uma entregável em ~½–3 dias de trabalho focado.**
Ordem privilegia **fim-a-fim feio antes de polido bonito** — princípio de §4.

**Frontends:** CLI nasce desde Fase 0 (frontend de desenvolvimento). Telegram
entra como nova Fase 7.5, depois do pipeline funcional — não antes, porque
debugar lógica de pipeline via Telegram é doloroso.

**Assets de marca:** Fase 2.5 (curta) dedicada à vinheta. Não acopla com Fase 0
(bootstrap) — assets de marca podem precisar refinamento depois de ver o
primeiro vídeo real, e não bloqueiam Fases 1–2.

### Fase 0 — Bootstrap (½ dia)

- [ ] `pyproject.toml`, `uv` setup
- [ ] estrutura de diretórios de §12
- [ ] `cli.py` com subcomandos vazios (apenas imprimem "TODO")
- [ ] `config.py` carregando YAMLs
- [ ] CONTEXT.md já criado ✅
- [ ] decisions.md já criado ✅

**Saída:** `contadinhos new test` cria diretório com a estrutura certa.

### Fase 1 — Tracer bullet com stubs (1 dia)

Pipeline ponta-a-ponta com **provedores fakes** (cada etapa retorna asset hardcodado).
Objetivo: ver o **fluxo** funcionando antes de tocar em qualquer API paga.

- [ ] `transcribe` retorna texto fixo
- [ ] `script` retorna roteiro JSON exemplo (com policy_check.verdict=ok)
- [ ] `images` copia placeholder PNG
- [ ] `video` copia placeholder MP4 (5s estático)
- [ ] `tts` copia placeholder WAV (silêncio)
- [ ] `assemble` concatena os MP4s placeholder
- [ ] `publish` imprime "would upload to YouTube"

**Saída:** `contadinhos run stories/test/` produz `final.mp4` (trash) sem custo.

### Fase 2 — Roteirista real + transcrição real (1–2 dias)

- [ ] Whisper (OpenAI API ou local) integrado
- [ ] LLM roteirista (Claude/GPT) com prompt em `config/script_prompt.md`
- [ ] Roteiro JSON validado por pydantic
- [ ] Pré-gate funcionando (campo `policy_check` populado pelo LLM)
- [ ] Pré-gate `review_required` bloqueia CLI e pede decisão humana

**Saída:** `contadinhos script stories/<id>/` gera roteiro válido a partir de áudio real.

### Fase 2.5 — Assets de marca (½ dia)

Sub-fase curta dedicada a gerar os ativos visuais **estáticos** que entram em
todo vídeo, antes do pipeline pegar imagens de roteiro. Mantém o pipeline
"funções puras sobre o roteiro" — assets de marca vivem fora dele.

- [ ] Vinheta abertura (2s) — Nano Banana com prompt de identidade do canal + Pillow pra finalizar texto
- [ ] Vinheta fechamento (3s) — mesmo padrão
- [ ] (opcional, ver nota abaixo) Retrato canônico da Clarinha em `assets/characters/clarinha.png`
- [ ] Salvar vinhetas em `assets/intro.mp4` e `assets/outro.mp4` (renderização final via ffmpeg)
- [ ] Documentar prompt usado em `docs/reference/brand-prompts.md` pra reproduzir se quiser regenerar

> **Nota — retrato canônico da Clarinha:** ficou **fora desta fase por padrão**
> consistente com Lote 6 (Nano Banana T2I puro, sem reference image). Se quiser
> incluir desde já, é só gerar 1 imagem PNG aqui e a Fase 3 passa a usar ela
> como `image=` quando o roteiro mencionar a Clarinha. Reabertura está em §15
> como galho de calibração — se a Clarinha "drifar" entre os primeiros 5 vídeos,
> volta pra cá e adiciona.

**Saída:** `assets/intro.mp4` + `assets/outro.mp4` prontos. (Opcional:
`assets/characters/clarinha.png`.)

### Fase 3 — Imagens-chave (1 dia)

- [ ] `ImageGenerator` interface (`core/images/base.py`)
- [ ] **Nano Banana** implementado em `core/images/nano_banana.py` via `google-genai` (Vertex AI)
- [ ] 4 candidatas por imagem-chave do roteiro (1 chamada com `number_of_images=4` se suportar; senão 4 chamadas paralelas)
- [ ] CLI mostra grid e pede escolha humana (`open` no macOS abre as 4 candidatas no Preview)
- [ ] Escolhida vai pra `images/<personagem>/chosen.png` (cópia, não symlink — robusto a mover)

**Saída:** roteiro tem todas as imagens-chave aprovadas.

### Fase 4 — Geração de vídeo (2–3 dias)

- [ ] `VideoGenerator` interface (`core/video/base.py`)
- [ ] **Veo 3.1** implementado em `core/video/veo.py` — **porta direta de `veo3/generate.py`**:
  - Reaproveita: padrão de polling de operação, `extract_last_frame` ffmpeg, chaining `image=` para next clip, `negative_prompt`
  - Adapta: cenas curtas (8s × ~10 cenas) em vez de 3 longas; modo I2V quando `imagem_chave_ref` setada, T2V quando não
  - ADC (`gcloud auth application-default login`) configurado uma vez, persiste
- [ ] Kling 2.0 implementado em `core/video/kling.py` (alternativa)
- [ ] Provider escolhido em `config/providers.yaml` (`video.provider: veo`)
- [ ] `cost_ledger.json` populado com custo nominal mesmo se for crédito
- [ ] Teto por-vídeo ativo
- [ ] Após porta concluída: deletar `veo3/` ou mover pra `docs/reference/`

**Saída:** roteiro vira ~10 clipes MP4 em `clips/`. Vídeo ainda mudo.

### Fase 5 — TTS + montagem (1–2 dias)

- [ ] `TTSProvider` interface
- [ ] ElevenLabs implementado
- [ ] FFmpeg concat + crossfade + drawtext + mix com música
- [ ] Vinheta intro/outro adicionada
- [ ] Output 1080p MP4 H.264/AAC

**Saída:** `final.mp4` com narração e música real.

### Fase 6 — Pós-gate multimodal (1 dia)

- [ ] LLM multimodal (Gemini 2.5 Flash padrão; configurável) recebe samples do MP4
- [ ] Atualiza `policy_check` no roteiro com flags pós
- [ ] Bloqueia upload se `verdict=review_required`

**Saída:** vídeos visualmente quebrados não chegam pro upload.

### Fase 7 — Upload YouTube (1–2 dias)

- [ ] OAuth desktop flow
- [ ] `videos.insert` com `selfDeclaredMadeForKids=true`
- [ ] `thumbnails.set` (com fallback)
- [ ] Metadata via template + `sinopse_curta`
- [ ] `publish_mode` configurável
- [ ] **Em paralelo:** submeter auditoria de compliance ao Google

**Saída:** `contadinhos publish` põe o vídeo no canal.

### Fase 7.5 — Frontend Telegram (2–3 dias)

- [ ] BotFather: criar `@contadinhosbot`, salvar token em `.env`
- [ ] `python-telegram-bot` ≥21 setup
- [ ] Allowlist de `chat_id` em `config/telegram.yaml`
- [ ] Handler de áudio: cria story, dispara transcribe + script
- [ ] Mensagem de roteiro com inline buttons (✅ / ✏️ / ❌)
- [ ] Wizard de imagens: media group + buttons por personagem
- [ ] Notificação de geração de vídeo (latência longa)
- [ ] Mensagem de pós-gate: final.mp4 + flags + buttons (🚀 / ❌ / 🎬)
- [ ] Botão "Promover pra public" (chama `videos.update`)
- [ ] Setup `launchctl` plist em `scripts/com.contadinhos.bot.plist` pra auto-restart
- [ ] CLI continua funcionando em paralelo (sanity check)

**Saída:** você manda áudio do iPhone, recebe vídeo no chat, promove com 1 toque.

### Fase 8 — Calibração (semanas 4–8)

- [ ] Rodar 10–20 vídeos reais
- [ ] Anotar falsos-positivos/negativos do pré e pós-gate
- [ ] Ajustar prompts em `config/policy.yaml`
- [ ] Decidir sobre migrar `publish_mode` → `direct_public`
- [ ] Decidir sobre escalar cadência

**Saída:** pipeline estável, decisão informada sobre próximo regime.

### Dependências entre fases

```
Fase 0 → Fase 1 → Fase 2 → Fase 2.5 → Fase 3 → Fase 4 → Fase 5 → Fase 6 → Fase 7 → Fase 7.5 → Fase 8
                              │
                              └─ paraleliza com Fase 3 se quiser
                                 (assets de marca não dependem de imagens-chave)
```

Solo, ordem linear é mais simples. Fases 2.5 e 3 podem rodar em qualquer ordem
ou em paralelo.

**Fase 7.5 não bloqueia Fase 8.** Se você quiser usar só CLI durante calibração,
pula 7.5 — Telegram bot é conforto, não requisito de qualidade do canal.

---

## 14. Backup e retenção do `stories/`

🤖→👤 **Decidido (sessão 2026-05-04):** rclone → Google Drive, retenção em
duas camadas (full nos primeiros 30 dias, depois fontes-e-finais).

### 14.1 Sincronização

| Item | Decisão |
|---|---|
| Tool | `rclone` (backend `drive:`) |
| Destino | Google Drive — pasta `Backup/contadinhos/` (assinatura existente) |
| Cadência | 1×/dia via `launchctl` (mesmo runner do bot Telegram) |
| Comando base | `rclone sync ~/contadinhos drive:Backup/contadinhos --backup-dir drive:Backup/contadinhos.versions/$(date +%Y%m%d) --exclude-from .rcloneignore` |
| Exclusões (`.rcloneignore` na raiz) | `.git/`, `.venv/`, `.secrets/`, `__pycache__/`, `*.pyc`, `veo3/.venv/`, `assets/music/` (recuperável da YT Audio Library) |

**Por quê rclone (e não Drive desktop app):**
- Controle do *quando* — não corre risco de capturar arquivo no meio de escrita do ffmpeg.
- `--backup-dir` versiona deletes em `drive:Backup/contadinhos.versions/<date>/` → defesa real contra `rm -rf` acidental.
- Independe da Drive desktop app; sobrevive a updates de macOS/Drive.

### 14.2 Retenção em duas camadas

🤖→👤 **Decidido:** primeiros 30 dias = backup full; depois rotaciona pra "só fontes e finais".

| Janela | Conteúdo backupado | Tamanho típico/story |
|---|---|---|
| Story criada nos **últimos 30 dias** | **Tudo:** `audio.m4a`, `transcript.txt`, `roteiro.json`, `images/*`, `clips/*`, `audio/*`, `final.mp4`, `policy_check_post.json`, `cost_ledger.json`, `upload_result.json` | 50–150 MB |
| Story criada há **>30 dias** | **Fontes e finais:** `audio.m4a`, `roteiro.json`, `images/<personagem>/chosen.png`, `final.mp4`, `cost_ledger.json`, `upload_result.json`. Apaga local: `candidate_*.png`, `clips/*`, `audio/*` | 5–25 MB |

Implementação: script `scripts/rotate_stories.py` rodado 1×/semana via launchctl. Lê data do dir `<YYYY-MM-DD>-<slug>`, se >30 dias apaga intermediários. Próximo `rclone sync` propaga o delete (versionado).

**Por quê:** primeiros 30 dias você vai querer poder retomar / regerar cena / inspecionar custo. Passado isso, regerar do zero é aceitável (e raro).

### 14.3 Restauração

Documentar comando único no `README.md`:

```bash
rclone sync drive:Backup/contadinhos ~/contadinhos --exclude-from .rcloneignore
```

Recupera tudo menos secrets (roda OAuth de novo, custa 1 minuto) e venv (recria com `uv venv`).

### 14.4 Riscos aceitos

- **Comprometimento da conta Google** = perda total (Veo credits + canal @contadinhos + backup Drive). Único asset que **não está** na conta Google é o token do bot Telegram (registrado em `.env`, fora do backup). Mitigação registrada em §16.
- **Janela `--backup-dir`:** se você não notar um delete acidental em poucos dias, a versão antiga vai sumindo do `.versions/<date>/`. Solução posterior: cron mensal arquivando `.versions/` num zip retido 6 meses. **YAGNI até a primeira perda real.**

---

## 15. Bar de qualidade pra promover unlisted → public

🤖→👤 **Decidido (sessão 2026-05-04):** **checklist explícito** antes da promoção
manual. Registrado por vídeo em `upload_result.json` como `quality_review`.

### 15.1 Hard fails (qualquer um → não promove)

Disparam decisão imediata: refazer cena específica / refazer vídeo todo /
abandonar. Não há override "promover mesmo assim" pra hard fails.

1. **Glitch visual** em rosto/mãos do protagonista (anatomia errada, dedos extras, olho deslocado)
2. **Vinheta quebrada** (corte mal feito, áudio cortado, texto errado)
3. **Áudio dessincronizado** com vídeo (delay >0,5s perceptível)
4. **Texto na tela** com typo, encoding quebrado, ou off-screen
5. **Tom sombrio/assustador** emergente (mesmo que pós-gate tenha passado)

### 15.2 Soft fails (decide caso-a-caso)

Você marca, mas pode promover mesmo assim. Registro vira histórico de calibragem.

6. **Estilo aquarela** menos vibrante / mais "render genérico de IA" que o padrão do canal
7. **Narração** ok mas sem brilho (ritmo, entonação)
8. **Duração** apertada/longa demais pra atenção de 3 anos
9. **Final** abrupto (corte sem fechamento)
10. **Música de fundo** muito alta vs narração

### 15.3 Critério pra promover

- Zero hard fails (1–5 todos `false`)
- Soft fails (6–10) marcados não bloqueiam, só registram
- Você assistiu o vídeo **inteiro** ao menos uma vez antes da promoção

### 15.4 Schema do registro

Adicionado a `upload_result.json` no momento da promoção:

```json
"quality_review": {
  "reviewed_at": "2026-05-08T22:14:00-03:00",
  "watched_full": true,
  "hard_fails": [],
  "soft_fails": [6, 8],
  "promoted": true,
  "notes": "aquarela ficou meio amarelada nas cenas 4-5; ainda assim aprovado"
}
```

**Por quê o registro:**
- **Calibragem do pós-gate** (Fase 8). Após 10–20 vídeos, cruzar `quality_review.hard_fails` com o `policy_check` do pós-gate revela onde o judge falha — input direto pra ajustar prompts em `config/policy.yaml`.
- **Anti-condescendência.** Vídeo 23 cansado às 23h tem mesmo crivo do vídeo 1.
- **Custo humano:** ~30s de marcação no CLI/bot. Dentro do orçamento de revisão humana (§4).

### 15.5 UX nos frontends

- **CLI:** comando `contadinhos publish` mostra os 10 itens em prompt interativo (typer + checkbox), confirma "watched_full?", grava `quality_review`, então pergunta "promover agora? [y/N]".
- **Telegram:** bot manda mensagem com `final.mp4` + 10 botões inline (toggle por item) + botão "✅ assisti inteiro". Quando todos os hard fails forem `false` e `watched_full=true`, libera botão "🚀 promover pra public".

### 15.6 Isolamento de config

Lista dos 10 itens mora em `config/quality_bar.yaml` (princípio §4). Adicionar
item 11 ou ajustar texto = mexer config, não código. Os índices numéricos
viram identificadores estáveis no histórico.

---

## 16. Versionamento de prompts (snapshot por story)

🤖→👤 **Decidido (sessão 2026-05-04):** git do `config/` + **snapshot literal**
dos prompts em cada `stories/<id>/prompts_snapshot.json`. Sem versionamento
semântico nominal (bump manual). Combina rastreabilidade direta com history
de evolução.

### 16.1 O que é snapshot por story

No início de cada etapa que consulta prompt em `config/`, o código faz cópia
literal do prompt usado e grava em `prompts_snapshot.json` da story. Quando o
pipeline termina, o snapshot está completo e congelado — nunca é reescrito.

Resultado: **cada vídeo gerado carrega no diretório os prompts que o produziram.**
Comparação entre vídeos vira leitura direta dos snapshots.

### 16.2 Schema do snapshot

```json
// stories/2026-05-04-raposa-curiosa/prompts_snapshot.json
{
  "captured_at": "2026-05-04T22:30:12-03:00",
  "config_git_sha": "a3b9c12",
  "snapshots": {
    "script": {
      "system_prompt": "Você é um roteirista de histórias infantis...",
      "style_string": "aquarela / livro infantil ilustrado, paleta pastel...",
      "model": "claude-opus-4.7"
    },
    "image_key_clarinha": {
      "prompt": "uma menininha de cabelo cacheado castanho...",
      "model": "gemini-2.5-flash-image"
    },
    "post_gate": {
      "system_prompt": "Você analisa vídeos infantis pra...",
      "model": "gemini-2.5-flash"
    },
    "veo_negative_prompt": "blurry, low quality, jump cuts..."
  }
}
```

`config_git_sha` é o SHA do commit ativo do diretório `config/` no momento da
captura — facilita correlacionar com o git log se quiser ver o diff entre dois
vídeos.

### 16.3 Por quê não versionamento semântico (`script_v3.md`)

Versionamento nominal exigiria disciplina de "bumpar versão sempre que mudar".
Em projeto solo pessoal, essa disciplina escala mal — após 6 meses, "v3" vai
conter 5 mudanças não documentadas e o sistema fica pior do que git puro.
Snapshot lazy é robusto a esquecimento: o código sempre copia, você nunca
esquece.

### 16.4 Implementação

- Loader único `core/config.py` carrega prompts e expõe método
  `snapshot(story_dir, key, value)` que faz append idempotente.
- Cada chamada LLM passa pelo loader → snapshot é gravado **antes** da chamada,
  garantia mesmo se a chamada falhar.
- `prompts_snapshot.json` entra no backup (§14.1) e nunca é mexido após
  congelado.

### 16.5 Snapshot captura prompt **renderizado**, não template

🤖→👤 **Decidido (sessão 2026-05-07):** `prompts_snapshot.json` guarda o
**texto final que foi para o LLM**, não o template fonte.

**Exemplo:**
- Source `config/prompts/script.md`: `"Você é um roteirista para crianças de {{idade}} anos. Estilo: {{style_string}}."`
- Snapshot na story: `"Você é um roteirista para crianças de 3 anos. Estilo: aquarela / livro infantil ilustrado, paleta pastel..."`

**Por quê renderizado:**
- Reproduz literal o que rodou — ler o snapshot 6 meses depois não exige saber valor das variáveis ativas.
- Calibração de prompts (§7.5, §15.6) muda variáveis frequentemente; snapshot virar "depende" derrota o propósito.
- Custo de armazenamento: irrisório (cada prompt < 5KB).

`config_git_sha` no snapshot continua útil pra cruzar com o template fonte
quando você quer ver "o que mudou no template entre vídeo X e vídeo Y" —
mas o snapshot por si só é auto-contido.

### 16.6 Isolamento de config

Os prompts vivem em `config/prompts/` (subdir dedicada). Cada um em arquivo
próprio (`script.md`, `post_gate.md`, `style.md`, etc.) — facilita git diff e
PR-style review mental quando ajustar.

---

## 17. Operação do bot Telegram (sleep, idempotência, crash recovery)

🤖→👤 **Decidido (sessão 2026-05-04):** três políticas combinadas pra robustez
do bot rodando local em macOS via `launchctl`.

### 17.1 Política de sleep do Mac

🤖→👤 **(A) Bloqueio total de sleep enquanto o bot estiver rodando.**

Implementação: `caffeinate -dims` envolvendo o processo do bot no `launchctl`
plist. Tela apaga normal, sleep do display fica permitido; CPU/disco ficam
acordados.

```xml
<!-- ~/Library/LaunchAgents/com.contadinhos.bot.plist (excerto) -->
<key>ProgramArguments</key>
<array>
  <string>/usr/bin/caffeinate</string>
  <string>-dims</string>
  <string>/path/to/.venv/bin/python</string>
  <string>-m</string>
  <string>contadinhos.frontends.telegram</string>
</array>
<key>KeepAlive</key>
<true/>
<key>RunAtLoad</key>
<true/>
```

**Por quê:** seu requisito é "deixar rodando" (Lote 4). Latência pra acordar
do sleep + processar fila empilhada degrada UX. Custo energético de Mac
M-series acordado idle é ~5–10W (tela apagada). Aceitável até VPS (§18).

### 17.2 Idempotência via `update_id`

🤖→👤 **Bot persiste estado mínimo em `.bot_state.json` na raiz.**

```json
{
  "last_processed_update_id": 42891,
  "last_seen_at": "2026-05-04T22:30:00-03:00",
  "current_story_id": null,
  "current_story_started_at": null
}
```

**Comportamento:**
- Antes de processar update do Telegram, checa `update.update_id > last_processed_update_id` — senão, skip silencioso.
- Após processar, atualiza `last_processed_update_id` (atomicamente: write em arquivo temporário + rename).
- Resolve duplicação por restart, race de polling, ou qualquer reentrada da event loop.

`.bot_state.json` **entra no backup** (§14.1) — restaurar em outra máquina retoma do mesmo ponto.

### 17.3 Recovery de story em curso após crash/restart

🤖→👤 **(C) Decisão humana via Telegram.**

Quando o bot sobe e detecta `current_story_id != null`, em vez de abortar ou
tentar inferir, manda **mensagem de recuperação** no chat:

> 💥 Reiniciei durante a story `2026-05-04-raposa-curiosa` (gerando há 12 min).
> O que faço?
>
> [✅ Tentar continuar daqui]  [❌ Abandonar story]

Comportamento:
- **Continuar:** bot lê o filesystem (`stories/<id>/`), identifica última etapa concluída (qual arquivo já existe), retoma da próxima.
- **Abandonar:** bot zera `current_story_id`, libera fila. Story fica em disco (você inspeciona/apaga manual depois).

**Por quê C:** casa com o princípio explícito de "humano sempre decide nos
gates críticos" (§7.3). Recovery automático seria forte tentação de
complexidade silenciosa, com risco de cobrança duplicada (Veo job server-side
continua mesmo se bot desistir local).

### 17.4 Custo aceito server-side

Crash durante geração Veo deixa o job rodando server-side com cobrança até
completar. Mitigação possível (não implementada agora, YAGNI): chamar
`operations.cancel` da Vertex AI no startup quando há `current_story_id` —
**mas** Vertex pode não interromper job já em vôo. Decisão pragmática:
**aceitar a cobrança eventual e mover.** Reabrir se virar dor real.

---

## 20. Práticas de engenharia (Harness engineering + TDD)

🤖→👤 **Decidido (sessão 2026-05-06):** o codebase é construído como
**harness engineering** — desenhado pra ser navegável e modificável tanto
por humano quanto por agente IA. Features novas entram via **TDD
red-green-refactor**.

### 20.1 Harness engineering — princípios concretos

Aplicação direta do que já está espalhado em §4, §9, §12 — consolidado
aqui pra virar critério explícito quando alguém (humano ou agente) abre
PR no projeto:

| Princípio | Manifestação prática | Já documentado em |
|---|---|---|
| **Pipeline core nunca importa frontends** | `core/` não conhece `frontends/`; só funções puras sobre `stories/<id>/` | §9.1, §12.2 |
| **Contratos explícitos entre etapas** | Roteiro JSON é **o** contrato; pydantic schemas em `core/schemas.py` | §3, §3.1 |
| **Funções puras sobre filesystem** | Cada etapa lê arquivos do dir da story, escreve novos. Sem estado em memória entre comandos. | §9.6 |
| **Filesystem-as-state** | Sem DB. Estado = arquivos em `stories/<id>/`. Debugável trivialmente: `ls stories/<id>/`. | §9.6 |
| **Provider-agnostic via interface** | `VideoGenerator`, `TTSProvider`, `ImageGenerator` em `base.py`; impls concretas plugáveis | §4, §5 |
| **Config isolada da lógica** | YAML em `config/`; código nunca importa config como módulo Python | §4, §7.5, §15.6, feedback memory `isolar_config_mutavel` |
| **Snapshots imutáveis por execução** | `prompts_snapshot.json` + `cost_ledger.json` em cada story; nunca reescritos | §11.3, §16 |
| **`next_action` como contrato de status** | `Story.next_action()` calcula a partir do que existe no dir; CLI/Telegram leem isso pra orientar UX | §9.2, §9.6 |
| **CLI subcommands granulares e idempotentes** | `transcribe`, `script`, `images`, ... cada um isolado, resumível, testável independente | §9.2 |
| **Comandos resumíveis** | Reentrar comando que já rodou = no-op (ou re-aproveita). `chosen.png` é cópia, não symlink (§"Fase 3"). | §13 (Fase 3) |

**Regra de ouro:** se uma feature nova quebra qualquer linha desta
tabela, abrir grelha antes de implementar. Não burlar silenciosamente.

### 20.2 TDD por feature — red-green-refactor

🤖→👤 **Decidido:** toda feature substancial entra via TDD. Etapas baratas
(rename, mover linha de config) ficam fora.

**Fluxo padrão:**

1. **Red:** escreve teste que descreve o comportamento desejado. Roda → falha por motivo certo (não por NameError; o teste tem que **chamar** o código que não existe ainda).
2. **Green:** implementa o **mínimo** que faz o teste passar. Resista à tentação de generalizar — features especulativas sem teste são proibidas (alinhado com instrução geral "Don't add features beyond what the task requires").
3. **Refactor:** com o teste verde como rede, refatora pra deixar bonito (extrair função, renomear, consolidar duplicação). Roda teste a cada passo.

**Granularidade do teste:**

- **Integração antes de unit.** Primeiro teste de uma feature é sempre o **caminho feliz ponta-a-ponta** com fakes. Só depois, testes unitários pra ramos do código.
- **Um teste = uma asserção principal.** Múltiplas verificações no mesmo teste viram múltiplos testes.
- **Nome do teste descreve o comportamento, não o método.** `test_pre_gate_bloqueia_cena_com_violencia` > `test_pre_gate_call`.

**O que **não** testar:**

- Wrappers triviais sobre SDK (`elevenlabs.generate(...)` já é testado pelo SDK).
- Layout de YAML de config (config é dado, não código).
- Strings de prompt (são dado; viram fixture, não asserção).

### 20.3 Estrutura de testes

```
tests/
├── contracts/                 # asserções compartilhadas Fake ↔ Real (ver §20.6 a)
│   ├── video_generator.py     # class VideoGeneratorContract
│   ├── tts_provider.py
│   ├── image_generator.py
│   ├── roteirista.py
│   ├── pre_gate.py
│   ├── post_gate.py
│   └── youtube_uploader.py
├── unit/                      # determinístico, < 100ms cada, sem rede
│   ├── test_schemas.py        # pydantic do roteiro, policy_check
│   ├── test_story_io.py       # Story.create / .load / .next_action
│   ├── test_fake_video.py     # subclassa VideoGeneratorContract com Fake
│   ├── test_pre_gate_logic.py # parsing do retorno do LLM, agregação de flags
│   ├── test_cost_ledger.py    # soma, paid_via, pre_flight estimate
│   └── ...
├── integration/               # toca filesystem real, pode usar fakes externos
│   ├── test_pipeline_with_fakes.py   # ponta-a-ponta com Fake* providers
│   ├── test_assemble_ffmpeg.py       # ffmpeg real, asserta duração e codec
│   ├── test_real_veo.py              # @pytest.mark.real_provider, mesmo contract
│   ├── test_real_elevenlabs.py       # @pytest.mark.real_provider
│   ├── test_telegram_state_machine.py
│   └── ...
├── fixtures/
│   ├── roteiros/
│   │   ├── valido_minimo.json
│   │   ├── valido_completo.json
│   │   ├── invalido_sem_cenas.json
│   │   └── violencia.json     # caso de pré-gate review_required
│   ├── regressions/           # bugs reais capturados (cresce com a operação)
│   │   └── s4-veo-codec-divergente.json
│   ├── audio/
│   │   ├── silencio_30s.m4a
│   │   └── historia_real.m4a  # gitignored se sensível
│   ├── images/
│   │   └── placeholder.png
│   └── video/
│       └── placeholder_5s.mp4
└── fakes/                     # test doubles (ver §20.4)
    ├── fake_llm.py
    ├── fake_image_generator.py
    ├── fake_video_generator.py
    └── fake_tts.py
```

### 20.4 Test doubles (Fake providers)

🤖→👤 **Decidido:** cada `*Provider` / `*Generator` no core tem **Fake**
correspondente em `tests/fakes/`. Fakes são test doubles **completos**, não
mocks parciais.

| Real | Fake (em `tests/fakes/`) | Comportamento |
|---|---|---|
| `core/script/llm.py::Roteirista` | `FakeRoteirista` | Lê fixture `roteiros/valido_completo.json` e devolve. Custo zero, determinístico. |
| `core/images/nano_banana.py::NanoBananaGenerator` | `FakeImageGenerator` | Copia `fixtures/images/placeholder.png` 4× e devolve. |
| `core/video/veo.py::VeoGenerator` | `FakeVideoGenerator` | Copia `fixtures/video/placeholder_5s.mp4`, ignora prompt. |
| `core/tts/elevenlabs.py::ElevenLabsTTS` | `FakeTTS` | Gera WAV de silêncio com duração `len(narracao_caracteres) * 0.05s`. |
| `core/policy/post_gate.py::PostGate` | `FakePostGate` | Retorna `verdict=ok` por padrão; aceita override no constructor pra forçar `review_required` em testes. |
| `core/upload/youtube.py::YouTubeUploader` | `FakeYouTubeUploader` | Grava `upload_result.json` com `videoId="fake-12345"`. |

**Por quê Fake e não Mock:**
- Fakes implementam a **interface inteira**, não só métodos chamados no
  teste. Refatoração que adiciona método à interface obriga atualizar fakes
  → CI pega contrato quebrado.
- Mocks (`unittest.mock.MagicMock`) cospem `MagicMock` em métodos não
  configurados → testes passam falsamente quando código novo chama método
  novo. Anti-padrão pra harness.

**Onde Fake plugar no Sprint 1:** as etapas "stub hardcoded" de §13 Fase 1
**são** os Fakes — só ficam em `tests/fakes/` em vez de `core/`. Comando
`contadinhos run` em modo dev usa Fakes via flag `--with-fakes` (lê de
`config/providers.yaml::testing.use_fakes` ou env `CONTADINHOS_FAKES=1`).

### 20.4.1 Convenção de markers de pytest

🤖→👤 **Decidido (sessão 2026-05-07):** quatro markers, todos declarados
em `pyproject.toml::tool.pytest.ini_options.markers`.

| Marker | Quando aplicar | Roda em CI? | Custo típico |
|---|---|---|---|
| (default — sem marker) | `tests/unit/**`: puro, < 100ms, sem rede, sem FS além de `tmp_path` | Sim | $0 |
| `integration` | `tests/integration/**`: toca FS real, ffmpeg real, providers via Fake | Sim | $0 |
| `real_provider` | Smoke real ponta-a-ponta com provider externo (Veo, ElevenLabs, YouTube...) | **Não** | $$ — rodar manual antes de fechar sprint |
| `slow` | Qualquer teste > 5s (mesmo unit ou integration) | Sim, mas pode skipar via `-m "not slow"` | varia |

**Combinação:** marker múltiplo é OK (`@pytest.mark.real_provider @pytest.mark.slow`).

**Comandos canônicos:**
- Local quick loop: `uv run pytest -m "not slow and not real_provider"` (default sem rede, rápido)
- Pré-PR: `uv run pytest -m "not real_provider"` (inclui slow, mas sem custo)
- Smoke real (DoD de sprint): `uv run pytest -m real_provider tests/integration/test_real_*.py`

### 20.5 Cassettes para chamadas reais (opcional, on-demand)

Pra testes que **precisam** validar contrato com API real (ex.: schema da
resposta do Veo mudou?), usar gravação-replay tipo VCR.

| Item | Decisão |
|---|---|
| Lib | `pytest-recording` (mais leve que `vcr.py` puro) ou `pytest-vcr`. Decidir na primeira necessidade real. |
| Quando gravar | Toda chamada **out-of-pocket** que CI vai replicar — gravar 1×, commitar cassette, CI replay sem custo. |
| Quando **não** gravar | Chamadas de calibração de prompt (mudam toda hora). Use Fake. |
| Onde guardar | `tests/cassettes/<test_name>.yaml`. Versionado no git **só se não tem dado sensível**. |
| Refresh | Manualmente — `pytest --record-mode=rewrite` quando souber que API mudou. |

**Cassettes são YAGNI até a primeira sprint que pisar em "tem que validar API real".** Provavelmente Sprint 2 ou 4. Não criar infra antes.

### 20.6 Fidelidade dos Fakes — evitar "passa em fake, quebra em real"

🤖→👤 **Decidido (sessão 2026-05-07):** o uso pesado de Fakes carrega
risco real de **falsa segurança** — testes verdes com app quebrada na
realidade. Cinco mitigações combinadas, todas obrigatórias:

#### (a) Contract tests compartilhados Real ↔ Fake

Para cada interface (`VideoGenerator`, `TTSProvider`, `ImageGenerator`,
`Roteirista`, `PreGateAuditor`, `PostGate`, `YouTubeUploader`, ...) existe
**uma** classe abstrata de teste em `tests/contracts/` que define as
asserções estruturais. **Tanto a impl Fake quanto a impl Real subclassam
e rodam exatamente o mesmo teste.**

```python
# tests/contracts/test_video_generator_contract.py
class VideoGeneratorContract:
    """Subclassada por TestFakeVideo e TestRealVeo. Mesmas asserções."""
    @pytest.fixture
    def generator(self): ...  # subclasse provê

    def test_i2v_retorna_mp4_existente(self, generator, tmp_path):
        out = generator.generate(prompt="x", duration_s=5, first_frame=PNG_FIXTURE)
        assert out.exists() and out.suffix == ".mp4"
        assert ffprobe(out)["duration"] == pytest.approx(5, abs=1)
        assert ffprobe(out)["codec_name"] == "h264"

    def test_t2v_sem_first_frame(self, generator):
        out = generator.generate(prompt="paisagem", duration_s=5)
        assert out.exists()

    def test_aborta_em_prompt_vazio(self, generator):
        with pytest.raises(ValueError):
            generator.generate(prompt="", duration_s=5)
```

```python
# tests/unit/test_fake_video.py
class TestFakeVideo(VideoGeneratorContract):
    @pytest.fixture
    def generator(self):
        return FakeVideoGenerator()

# tests/integration/test_real_veo.py  (com marker pytest.mark.real_provider)
@pytest.mark.real_provider
class TestRealVeo(VideoGeneratorContract):
    @pytest.fixture
    def generator(self):
        return VeoGenerator()
```

**Garantia:** se o Real cospe MP4 de duração ±1s do esperado, o Fake também
precisa cospir. Se o Real levanta `ValueError` em prompt vazio, o Fake
também. Refatoração que adiciona método à interface obriga atualizar
contract test → ambos lados ficam sincronizados.

#### (b) Boundary mínima — só APIs externas pagas são fakeadas

Lista do que **não** pode ser fakeado:

| Componente | Por quê real | Como rodar em teste |
|---|---|---|
| Pydantic schemas | Validação **é** a feature; mockar derrota | Sempre real |
| Filesystem (`stories/<id>/`, `chosen.png`, etc.) | Comportamento de IO **é** parte do contrato | `tmp_path` do pytest |
| ffmpeg | Mux/concat/drawtext têm muito edge case; mock vira ficção | Subprocess real, fixtures pequenas (5s) |
| `core/config.py` (loader) | Se o YAML tá errado, queremos saber | YAML real em `tests/fixtures/configs/` |
| `Story.next_action()` | Lógica pura sobre FS — não tem o que fakear | Sempre real |
| Pré-gate **prompt rendering** | O texto formatado **é** o produto | Asserção sobre string final |

Lista do que **pode** ser fakeado:
- LLM roteirista (Claude/Anthropic API)
- LLM auditor pré-gate
- Nano Banana (Vertex AI)
- Veo 3.1 (Vertex AI)
- Kling, Runway, ElevenLabs
- Gemini multimodal (pós-gate)
- YouTube Data API

**Regra:** se passa pela rede e custa dinheiro, é candidato a Fake. Tudo
mais é real no teste.

#### (c) Smoke test real ao fim de cada sprint (DoD)

Toda sprint a partir da Sprint 2 (a Sprint 1 só tem fakes mesmo) inclui no
DoD um item explícito:

> ✅ **Smoke real:** rodar pipeline ponta-a-ponta **sem `--with-fakes`** em
> uma story de teste. Tem que produzir o artefato esperado da sprint
> (roteiro real / imagens reais / vídeo real / upload real). Custo
> registrado no ledger sob `stories/smoke-<sprint-N>-<date>/`.

Se o smoke real quebra mas os testes verdes, o Fake mentiu — atualizar
contract test pra capturar a divergência e o Fake pra corresponder. **Não
fechar sprint até smoke real passar.**

#### (d) Corpus de regressão alimentado por falhas reais

Quando smoke real revelar bug que Fake não pegou:

1. Capturar fixture mínima do bug em `tests/fixtures/regressions/<sprint>-<short_name>.json` (ou .png/.mp4 conforme).
2. Adicionar caso ao contract test que **falha** com Fake atual.
3. Atualizar Fake pra reproduzir o modo de falha real.
4. Caso fica permanente — toda sprint futura roda contra ele.

Corpus cresce monotonicamente. Cada bug pego em produção vira teste novo.

#### (e) Fakes registram chamadas, testes asseram contratos de uso

Fake guarda histórico de chamadas pra permitir asserções tipo "core chamou
o provider com argumentos razoáveis":

```python
class FakeVideoGenerator:
    def __init__(self):
        self.calls: list[dict] = []  # histórico

    def generate(self, prompt, duration_s, first_frame=None):
        self.calls.append({"prompt": prompt, "duration_s": duration_s, "first_frame": first_frame})
        ...

# teste:
def test_video_recebe_prompt_estilizado(pipeline_with_fakes):
    pipeline_with_fakes.run(...)
    fake_video = pipeline_with_fakes.video_generator
    assert all("aquarela" in c["prompt"] for c in fake_video.calls)
    assert all(5 <= c["duration_s"] <= 10 for c in fake_video.calls)
```

Pega bugs onde core não tá montando o prompt direito — o Real falharia
silenciosamente (gera vídeo errado), o Fake aceita qualquer string. A
asserção do teste é o que captura a divergência.

---

**Resumo:** Fakes são meio, não fim. Boundary estreita (só APIs externas
pagas), Real e Fake compartilham o mesmo contract test, smoke real
obrigatório no DoD, corpus de regressão acumula bugs reais, e Fakes
registram chamadas pra teste asserir uso correto. Combinação cobre os
três modos de "fake mente":

| Modo de mentira do Fake | Mitigação |
|---|---|
| Fake retorna formato diferente do Real | Contract test compartilhado (a) |
| Fake aceita input que Real rejeita | Contract test + smoke real (a + c) |
| Core chama Fake com argumento errado e ninguém percebe | Asserção sobre `fake.calls` (e) |
| Fake estagna enquanto Real evolui | Smoke real periódico + corpus de regressão (c + d) |
| Tem comportamento crítico no boundary fakeado (FS, ffmpeg, schema) | Boundary mínima — esses são sempre reais (b) |

### 20.7 Aplicação por sprint

Cada sprint em `sprints.md` ganhou subseção **"Como implementar (TDD)"**
listando os testes a escrever **antes** das tasks de implementação. Ordem
canônica:

1. Escrever testes da subseção (red).
2. Rodar `uv run pytest tests/<nova_pasta>/` → todos falham.
3. Implementar tasks da sprint, rodando testes ao fim de cada task (green).
4. Refatorar com testes verdes como rede (refactor).
5. DoD da sprint inclui: **todos os testes desta sprint + os anteriores ainda passam**.

**Cobertura mínima por sprint:** 1 teste de integração + 2–3 testes
unitários por feature substancial. Não perseguir 100% de coverage —
perseguir **testes que falhariam se o comportamento quebrasse**.

---

## 18. Decisões explicitamente *recusadas* (registro pra não ressuscitar)

- ~~Manter voz do pai no vídeo final~~ — recusado: pivot pra anonimato total, TTS no lugar.
- ~~Trilho duplo "família privado + público anonimizado"~~ — recusado: saída única anônima.
- ~~T2V puro (sem imagem-chave)~~ — recusado: inconsistência intra-vídeo seria gritante.
- ~~Suno/Udio para música~~ — recusado por enquanto: YouTube Audio Library + curadoria resolve em canal pequeno.
- ~~Remotion para montagem~~ — recusado: complexidade React não justificada pra texto simples.
- ~~Estilo visual variável entre vídeos~~ — recusado: aquarela fixa, identidade de canal.
- ~~LLM-generated description/tags por vídeo~~ — recusado (§8.3): identidade de tom estável vence; template + slot wins.
- ~~Auto-retry em policy_check reprovado~~ — recusado (§7.3): humano sempre decide; auto-retry inflaciona custo silenciosamente.
- ~~Cadência "quase diário" (~30 vídeos/mês)~~ — recusado por enquanto (§11.1): realidade é 2–3/semana, escalar depois se quiser.
- ~~Scheduler/cron pra orquestração~~ — recusado (§9.2): on-demand é a verdade; scheduler seria over-engineering.
- ~~Agente LLM no leme da orquestração~~ — recusado (§9.2): cada etapa tem decisão humana; agente só intermedia mensagens sem benefício.

---

## 19. Galhos para reabrir depois da calibração (mês 2–3)

- **Pós-gate calibrado?** Avaliar taxa de falso-positivo e falso-negativo. Ajustar prompt do judge e/ou trocar modelo multimodal (Gemini ↔ Claude ↔ GPT-4o).
- **Migrar `publish_mode` pra `direct_public`?** Decidir após 20+ vídeos com pós-gate estável.
- **Aumentar cadência?** Se rotina sustentar, considerar 5/semana.
- **Abaixar teto por-vídeo Veo/Kling após calibração.** Teto inicial está propositalmente mais largo (US$80 Veo / US$30 Kling) pra não morder durante calibração (§11.2). Após 5–10 vídeos reais com custo nominal medido, abaixar pra valor que reflita realidade observada (provavelmente US$60 / US$25, mas pode ser outro). Critério: `p95(custo_real_observado) × 1.15`.
- **Subir tier do roteirista (`gpt-5-mini` → `gpt-5.5`)?** Default é mini (§3.3). Critério pra subir: após Sprint 7, se >1 roteiro com cena ilógica/incoerente em 10 vídeos. **Antes** investir em prompt (system prompt + few-shot + style guide). Subida = trocar `script.model` em `config/providers.yaml` + atualizar fallback em §3.3. Custo: 15× mais por roteiro (~US$0,005 → ~US$0,07).
- **Modelos Google em status preview** (decidido 2026-05-07). Veo 3.1 (`veo-3.1-generate-preview`) e Nano Banana 2 (`gemini-3.1-flash-image-preview`) estão em **preview**, não GA. Risco aceito: deprecation com aviso → trocar model id em `config/providers.yaml`. Justificativa: (a) Nano Banana 2 traz consistência de até 5 personagens, recurso direto pra Clarinha não drifar entre vídeos; (b) Veo 3.1 é a linha mais recente e qualidade é prioridade no canal infantil; (c) `gemini-2.5-flash` (GA estável) continua nos gates auditores onde estabilidade > qualidade marginal. Reabrir se: deprecation chegar, ou se 3.x sair de preview (atualizar config). Pré/pós-gate **não** mudam — ficam em GA.
- **Migrar de Gemini API key → Vertex AI + ADC.** Hoje (2026-05-07) usamos `GOOGLE_GENERATIVE_AI_API_KEY` direto pra Veo/Nano Banana/Gemini multimodal (§5). Vertex AI tem features que a Gemini API direta não cobre (quotas customizadas, audit logging, IAM granular, regional routing). Reabrir se: (a) precisar de quota acima do default da Gemini API, (b) compliance/audit virar requisito, (c) o crédito migrar pra Vertex. Migração: trocar `genai.Client(api_key=...)` por `genai.Client(vertexai=True)` + ADC (`gcloud auth application-default login`). Provider-agnostic protege — só muda o construtor.
- **Migrar Veo → Kling quando crédito Google esgotar?** Veo é default só enquanto há crédito (§5, §11.4). Quando esgotar: avaliar (a) qualidade real observada, (b) custo mensal sustentável (US$300+ vs US$100). Migração é trocar `video.provider` em `config/providers.yaml`.
- **Web UI ou Discord como terceiro frontend?** Pipeline core já está pronto pra plugar mais frontends. Reabrir só se Telegram + CLI não bastarem.
- **Migrar bot Telegram pra VPS dedicado.** Hosting inicial é local macOS via `launchctl` (§9.4). Quando o pipeline estabilizar e o Mac dormindo virar incômodo real, migrar pra VPS US$5–10/mês (DigitalOcean/Hetzner/Linode). Polling continua igual; só muda de máquina. Reabrir após Fase 8 (calibração).
- **Consistência visual da Clarinha entre vídeos** (e personagens recorrentes em geral). Hoje: Nano Banana T2I puro — cada vídeo gera Clarinha do zero, vai variar (cor de cabelo, vestido, idade aparente). Refinamento futuro: gerar **uma imagem-referência canônica** da Clarinha em `assets/characters/clarinha.png` na Fase 2.5 e usar como `image=` input do Nano Banana em todo I2I. Mesmo padrão pra personagens recorrentes (`personagem.recorrente: true` no roteiro). Reabrir se a Clarinha "drifar" demais entre os primeiros 5 vídeos.
- **Endurecer segurança da conta Google.** Conta Google carrega **três ativos críticos**: créditos Veo, canal @contadinhos, backup Drive (§14). Compromisso = catástrofe total. TODO operacional curto: ativar 2FA com app authenticator (gratuito, 5 min) ou YubiKey hardware (~US$50, mais robusto). **Fazer antes do primeiro upload pago.**
- **Arquivar histórico de `--backup-dir`** num zip retido 6 meses. Hoje versionamento de delete vive em `drive:Backup/contadinhos.versions/<date>/` indefinidamente — barato em termos de Drive, mas vira lixo. Cron mensal limparia. **YAGNI até a primeira perda real** (§14.4).
- **Adotar Supabase como camada de metadata.** Free tier generoso (500MB DB + 1GB storage + 2GB bandwidth). Casos de uso que justificam migrar do filesystem-puro:
  - **Web UI** (consulta cross-story sem listar diretórios)
  - **Dashboard de custo** (somar `total_usd_out_of_pocket` por mês/provider sem ler N JSONs)
  - **Sync entre Mac local e VPS** se bot migrar e CLI continuar local
  - **Histórico de prompts** (search nos `reviewer_note` dos `policy_check` reincidentes)
  Migração inicial seria espelhar `cost_ledger.json` e o resumo do `roteiro.json`
  numa tabela; blobs continuam no filesystem (ou Supabase Storage como upgrade
  posterior). **Reabrir quando o filesystem virar gargalo ou Web UI entrar.**
- **Chaining last-frame entre cenas (reabrir).** Hoje desligado por padrão (§3.2). Reabrir se Sprint 7 mostrar que "salto visual entre cenas" quebra fluxo da história pra criança. Caminho de reativação: flag `video.chain_first_frame: true` em `config/pipeline.yaml`. Considerar variante seletiva (`cena.chain_from_previous: bool` no schema do roteiro) pra chain só dentro de mesma sequência narrativa.
- **CI/CD em GitHub Actions.** 🤖→👤 (2026-05-07): **dispensado por enquanto.** Projeto é solo, repo privado. Custo do `.github/workflows/ci.yml` é baixo, mas: (a) `uv run pytest` local é hábito de TDD obrigatório (§20.2), (b) pre-commit hook simples cobre o esquecimento, (c) smoke real (§20.6 c) já é manual mesmo. Reabrir se: virar dois desenvolvedores, repo virar público, ou pyproject ganhar deps fragéis com matrix de Python. Caminho de reativação: GH Actions com `uv sync && uv run pytest -m "not real_provider"` em push (gratuito em repo privado até 2000 min/mês).
- **Custom TTS voice (clone)?** Se ElevenLabs default não convencer, considerar voz customizada — provider já abstrai.
- **Migrar audiência da filha pro YouTube Kids app?** Hoje (2026-05-06) ela re-assiste pelo YouTube clássico no device do pai. Risco: algoritmo de recomendação adulto pode sugerir conteúdo inadequado em sessão dela. Mitigações progressivas se virar incômodo: (a) playlist "tudo do canal contadinhos" + Restricted Mode da conta, (b) perfil supervisionado via Family Link, (c) YouTube Kids app puro (gate de indexação automática pode demorar semanas após primeiros uploads). Reabrir se aparecer recomendação ruim.
- **Música original (Suno)?** Se a curadoria YT Audio Library cansar e o canal crescer, reabrir.
- **Pedir aumento de quota YouTube?** Se algum dia bater 3+ vídeos/dia regulares.
