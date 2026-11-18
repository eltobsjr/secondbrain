---
name: secondbrain-devtrack
description: |
  Gera o log de sessão (devtrack) do projeto atual e salva no vault SecondBrain.
  
  Use esta skill sempre que o usuário pedir para:
  - "/devtrack"
  - "gerar o devtrack"
  - "criar o log da sessão"
  - "registrar o que foi feito"
  - "documentar a sessão"
  - ao final de uma sessão de implementação
  
  Também acionar proativamente quando o usuário disser "terminamos", "por hoje é isso",
  "pode encerrar" ou qualquer sinal de encerramento de sessão sem ter gerado o devtrack.
---

# SecondBrain — Devtrack

> **Vault:** antes de ler ou gravar, resolva o vault e os caminhos conforme `references/vault-resolve.md` (manifesto `_secondbrain.md`; se faltar, migração assistida sem mover nada). Neste arquivo, `{vault}` é a pasta do vault e `{devtrack}`, `{decisoes}`, `{features}`, `{prioridade}` etc. são os caminhos que o manifesto dá a cada papel (sem manifesto, valem os padrões).

Gera e salva o log de sessão no vault do projeto.

---

## Passo 0 — Fechar o ciclo da sessão anterior (se o motor existir)

O devtrack é um retrato de fim de sessão. Na prática, a grande maioria das caixas `- [ ]` que ele deixa abertas nunca mais aparece numa sessão seguinte: foram feitas ou largadas sem registro. Por isso, **antes de escrever o devtrack novo**, concilie o anterior. Com `$SB/xmem.py` (`references/vault-resolve.md`, seção 0):

```bash
python3 -I "$SB/xmem.py" board show --project <projeto> --status a-fazer,fazendo,bloqueado
python3 -I "$SB/xmem.py" reconcile <projeto>
```

Rode também `python3 -I "$SB/xmem.py" board revisao --project <projeto>` (revisão semanal: propõe o que fazer com os abertos de semanas que passaram) e `board agenda --project <projeto>` (o que está atrasado, vence hoje ou está chegando). Pergunte uma vez, em lote, o destino de cada pendência da sessão anterior: **feito**, **segue** ou **descartado** (com o motivo, em uma frase). O que segue e tem data recebe prazo e semana: `board plan <projeto> <id> --semana esta|proxima --prazo +3d`. O que o git confirma (nível A do `reconcile`) pode ser proposto como feito; níveis B e C só se o usuário concordar. Registre no quadro (`board move <projeto> <id> feito|descartado`). **Nunca reescreva o devtrack antigo.** Em vault sensível ou versionado o comando pede `--confirmo`: pergunte antes. Sem o motor, pergunte só pelas pendências do último devtrack.

## Passo 1 — Coletar contexto da sessão

Execute em paralelo:

```bash
# Data de hoje e do devtrack mais recente
date +%Y-%m-%d
ls {vault}/{devtrack}/ 2>/dev/null | sort | tail -1

# Arquivos modificados na sessão (staged + unstaged + untracked relevantes)
git diff --name-only HEAD 2>/dev/null
git diff --name-only --cached 2>/dev/null
git status --short 2>/dev/null

# Commits feitos nesta sessão (últimas 10 horas)
git log --oneline --since="10 hours ago" 2>/dev/null

# Caminho do vault
ls {vault}/{devtrack}/ 2>/dev/null | sort | tail -5
```

Também use a conversa atual como fonte primária: o que foi discutido, implementado, corrigido, decidido ou planejado nesta sessão.

**Verificar gap desde o último devtrack:**
A partir do nome do devtrack mais recente, extraia a data (`YYYY-MM-DD`). Se a diferença para hoje for maior que 3 dias, avise antes de continuar:

> "⚠️ O último devtrack foi em {data} ({N} dias atrás). Sessões sem registro podem ter perdido contexto. Vou gerar o devtrack de hoje — se quiser, posso também criar um devtrack resumido do período {data} → hoje."

Se o usuário quiser o devtrack do período, gere um único arquivo cobrindo o intervalo, usando git log como fonte principal.

---

## Passo 2 — Inferir o título

**Não pergunte o título ao usuário.** Infira a partir do que foi feito:

- Se foi implementação: use o nome da feature/componente principal
- Se foi correção de bugs: use o sintoma ou componente principal
- Se foi análise/planejamento: indique isso no título
- Se foram múltiplas coisas: escolha a mais significativa ou combine as 2 principais

**Exemplos de bons títulos:**
- `Implementação DocumentMoreResults no card de busca`
- `Correções de exibição do botão DocumentMoreResults`
- `Análise HU002 v1.5 e leitura HU004`
- `Redesign search page e responsividade`
- `Fases 1-6 submissão concluídas, audit HU002-new v1.4`

**Evitar:**
- `Sessão de trabalho`
- `Implementações diversas`
- `Fixes`

---

## Passo 3 — Gerar o devtrack

Use o formato de `references/devtrack-format.md`. Siga as regras abaixo:

### Nome do arquivo
```
YYYY-MM-DD - {Título inferido}.md
```

### Estrutura obrigatória

```markdown
---
tipo: devtrack
data: YYYY-MM-DD
commits: [{hashes curtos dos commits da sessão, se houver}]
---

# YYYY-MM-DD — {Título}

{Se foi sessão de análise sem código}: > Sessão de análise e planejamento. Sem implementação de código.

## O que foi feito

{Narrativa clara do que aconteceu. Pode ser em tópicos numerados se múltiplas iniciativas.
 Inclua o "por quê" das decisões, não só o "o quê" — o git diff já tem o o quê.}

---

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `caminho/completo/do/arquivo` | O que mudou e por quê |

## Status

- [x] {Cada coisa concluída}
- [ ] {Cada pendência em aberto}
```

**Onde vai a pendência.** Caixa `- [ ]` só para o que ainda vai ser feito. Não use caixa para pergunta (`...?`), para frase de estado ("nenhum commit feito", "não testado") nem para etapa de procedimento da sessão: escreva isso em texto. O quadro ignora pergunta e frase de estado em devtrack. Tarefa nova que você assume nesta sessão ganha prazo (`board plan` ou `board prazo`); sem prazo ela aparece como "sem prazo", nunca como atrasada. O que segue vivo vai também no `ESTADO.md` (Próximo passo, Bloqueios): se o estado vivo cita o item, ele continua aberto; se não cita e o item não reaparece em 14 dias de projeto, o quadro o oculta como superado.

### Modo curto

Sessão pequena (poucos arquivos, nenhuma decisão, nenhum bug relevante): gere só `## O que foi feito`, `## Status` e, se houver, `## Próximos passos`. Não encha seções por obrigação. Respeite também o `nomes.devtrack` e os `campos-extra.devtrack` do manifesto, se existirem.

### Seções opcionais (adicionar quando aplicável)

**Se corrigiu bugs:**
```markdown
## Bugs corrigidos

### Bug — {nome curto}

**Problema:** sintoma observado.
**Causa:** explicação técnica.
**Correção:** `arquivo` — o que foi mudado.
```

**Se tomou decisões técnicas não óbvias:**
```markdown
## Decisões técnicas

### {Nome da decisão}
**Contexto:** por que precisou decidir.
**Alternativas consideradas:** ...
**Decisão:** o que foi escolhido e por quê.
```

**Se há ações claras para a próxima sessão:**
```markdown
## Próximos passos

1. {Ação específica com contexto suficiente para retomar sem reler tudo}
```

---

## Passo 4 — Salvar o arquivo

Detecte o vault do projeto:
```bash
ls -d *SecondBrain/ 2>/dev/null
```

Salve o devtrack em `{vault}/{devtrack}/YYYY-MM-DD - {Título}.md`.

Se não encontrar o vault na raiz, procure no diretório pai ou pergunte ao usuário onde está o SecondBrain do projeto.

---

## Passo 4a — Atualizar o quadro (se o motor existir)

Se `$SB/xmem.py` existir, o quadro já mostra os `- [ ]` deste devtrack como cartões novos. Para o que foi **concluído nesta sessão**, mova para Feito (`python3 -I "$SB/xmem.py" board move <projeto> <id> feito`; ids em `board show --project <projeto>`) ou, se preferir, marque `- [x]` no devtrack seguinte (a origem concluída vence). O que ficou **bloqueado**, mova para `bloqueado --bloqueado-por "<motivo>"`. Em vault sensível ou versionado o comando pede `--confirmo`: pergunte antes. Se o projeto não tem `quadro.md` e o usuário não usa o quadro, pule sem perguntar. O quadro oculta por padrão o que é ruído, repetido ou superado (`board show --ocultos` lista, com o motivo).

## Passo 4b — Atualizar o ESTADO.md

Se o vault tem o papel `estado` (arquivo `ESTADO.md` ou o caminho do manifesto) — ou o módulo `estado` está ligado — **reescreva-o inteiro** conforme `references/estado-format.md`: Agora, Próximo passo, Bloqueios, Fatos voláteis (com data). Se o arquivo não existe e o módulo está ligado, crie-o. Se o projeto não usa o módulo, pule este passo sem perguntar.

## Passo 4c — Regenerar o INDEX.md

Se o vault tem o papel `indice`, regenere-o (sem modelo, só lê o manifesto e as notas):

```bash
python3 -I "$SB/build_index.py" {vault}
```

Em seguida atualize o índice da memória cruzada (incremental e barato; falha em silêncio se o `xmem` não existir):

```bash
python3 -I "$SB/xmem.py" index 2>/dev/null || true
```

Se os scripts não estiverem acessíveis, pule em silêncio; o `/audit` avisa índice desatualizado.

---

## Passo 5 — Confirmar

Após salvar, exiba:

```
✓ Devtrack salvo: {vault}/{devtrack}/YYYY-MM-DD - {Título}.md
{Se atualizou}: ✓ ESTADO.md atualizado

{Se houver pendências abertas}:
Pendências registradas:
- {lista dos checkboxes não marcados}
```

Não mostre o conteúdo completo do devtrack — o usuário pode abrir no Obsidian.
