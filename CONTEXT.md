# contadinhos — glossário de domínio

> Linguagem canônica do projeto. Quando termos aparecem em documentação,
> commits, prompts ou conversa, devem casar com este glossário.
> Atualizar inline conforme novos termos forem cravados em sessões de grelha.

## Termos

### Roteiro (JSON)
Saída do LLM roteirista, contrato entre todas as etapas downstream.
Estrutura completa em `docs/decisions.md` §3.1. Cada etapa do pipeline é
**função pura sobre o roteiro**.

### Imagem-chave
Imagem estática gerada (Imagen 3 / Midjourney) que serve como first-frame
de uma cena I2V (image-to-video) ou como miniatura do vídeo no YouTube.
Cada personagem do roteiro tem ao menos uma imagem-chave.

### Cena
Unidade do roteiro. Tem `idx`, `modo` (`i2v` ou `t2v`), `prompt_visual`,
`narracao`, `duracao_s`. Cada cena gera um clipe de 5–10s no provedor
de vídeo.

### I2V / T2V
- **I2V** (image-to-video): cena gerada a partir de uma imagem-chave
  como first-frame. Usado quando há personagem.
- **T2V** (text-to-video): cena gerada só do prompt de texto. Usado pra
  paisagem pura, sem personagem fixo.

### Policy check
Gate de aprovação anti-conteúdo-impróprio, em **camada dupla**:

- **Pré-gate** — chamada LLM **separada** depois do roteirista, com persona
  de auditor estrito. Modelo barato (Haiku/Gemini Flash). Sobre o texto do
  roteiro JSON. Custo ~US$0,01–0,03. Pega risco narrativo (medo, violência,
  tema adulto). Separado do roteirista pra evitar conflito de interesse
  (autor não é juiz de si mesmo).
- **Pós-gate** — roda no MP4 final via LLM multimodal, sobre frame
  samples + áudio. Custo ~US$0,05–0,20. Pega modos de falha visuais
  (rosto distorcido, vibe sombria emergente) que o pré-gate não vê.

Reprovado em qualquer um → **bloqueia** e abre revisão humana (sem
auto-retry). Schema canônico em `docs/decisions.md` §1.

### Verdict
Resultado do policy check: `ok` | `review_required`.

### Reviewer note
Campo no `policy_check` preenchido pela revisão humana após
`review_required`. Vira histórico — cinco vídeos depois, vai mostrar
padrões pra recalibrar prompts.

### Made for kids
Flag obrigatória do YouTube pra conteúdo direcionado a crianças (COPPA).
Todo vídeo deste projeto sobe com essa flag ativa. Restringe
funcionalidades (sem comentários, sem notificações, sem ads
personalizadas) — aceito por design.

### Anonimato por design
Saída final **nunca** carrega voz do pai, imagem da filha, ou qualquer
identificação real. Personagem-menininha é **fictícia genérica**, com
nome inventado fixo. Detalhe em `docs/decisions.md` §1.

### VideoGenerator / TTSProvider
Abstrações no código que permitem trocar provedor de vídeo
(Kling / Veo 3.1 Lite|Fast / Runway / Seedance) e TTS
(OpenAI `gpt-4o-mini-tts` default / Gemini 2.5 Flash TTS / ElevenLabs legacy)
sem mexer no resto do pipeline. Provider ativo selecionável via
`config/providers.yaml`. Princípio: provider-agnostic onde o custo de
troca é alto.

### contadinhos (canal)
Nome do canal YouTube (lowercase, como configurado no Studio) onde os
vídeos são publicados. Handle `@contadinhos` (URL
`youtube.com/@contadinhos`). Diminutivo afetivo em pt-BR. Tagline:
"Histórias em aquarela para crianças". Marca estável — vinheta
intro/outro pré-gerada, descrição padrão em template, capitalização
lowercase consistente em todo lugar que referencia o canal.

### Clarinha
Nome fictício fixo da personagem-menininha que representa a filha real
nos roteiros. Nunca se refere à filha real; aparece em texto/narração;
visualmente é uma menininha genérica gerada por IA (sem aparência da
filha real).

### Story (diretório de história)
Unidade de trabalho do pipeline. Cada história ocupa um diretório
`stories/<YYYY-MM-DD>-<slug>/` com toda a entrada, intermediários e
saída. Estado vive no filesystem — comandos da CLI são puros sobre esse
diretório, qualquer falha é resumível.

### Sinopse curta
Campo do roteiro JSON (1–2 frases) que alimenta a descrição YouTube via
template. Produzido pelo LLM roteirista no mesmo passo do roteiro.

### Cost ledger
Arquivo `cost_ledger.json` em cada `stories/<id>/` que registra o custo
de cada etapa. Soma dos ledgers do mês = custo mensal. Define se o teto
foi ultrapassado.

### Pipeline core
Biblioteca Python headless em `src/contadinhos/core/`. Implementa todas as
etapas do pipeline (transcribe → script → images → video → tts → assemble →
policy → upload). **Nunca** importa frontends; expõe funções puras sobre
o diretório de uma Story. Múltiplos frontends podem chamá-lo
concorrentemente (com fila simples no filesystem).

### Frontend
Camada de interação com o usuário. Vive em `src/contadinhos/frontends/`.
Cada frontend é um módulo independente que importa o pipeline core e
renderiza UI próprio. Frontends ativos:
- **CLI** (`frontends/cli/`) — typer subcommands. Frontend de
  desenvolvimento e debug primário.
- **Telegram** (`frontends/telegram/`) — bot em modo polling rodando
  localmente via `launchctl`. Frontend de operação ("set and forget").

Princípio: pipeline core nunca conhece frontends. Adicionar frontend novo
(Web, Discord) = novo módulo, zero alteração no core.

### Publish mode
Configuração em `config/youtube.yaml` que controla privacidade do upload:
- `unlisted_review` (default) — sobe unlisted, humano promove.
- `direct_public` — sobe público direto. Habilitar só após calibração.
- `private_only` — sobe privado (forçado pela API enquanto projeto não auditado).

### Pré-gate / Pós-gate
Ver entrada **Policy check**.
