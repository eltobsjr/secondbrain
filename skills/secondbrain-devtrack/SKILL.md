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

Gera e salva o log de sessão no vault do projeto.

---

## Passo 1 — Coletar contexto da sessão

Execute em paralelo:

```bash
# Data de hoje
date +%Y-%m-%d

# Arquivos modificados na sessão (staged + unstaged + untracked relevantes)
git diff --name-only HEAD 2>/dev/null
git diff --name-only --cached 2>/dev/null
git status --short 2>/dev/null

# Commits feitos nesta sessão (últimas 10 horas)
git log --oneline --since="10 hours ago" 2>/dev/null

# Caminho do vault
ls *SecondBrain/devtrack/ 2>/dev/null | sort | tail -5
```

Também use a conversa atual como fonte primária: o que foi discutido, implementado, corrigido, decidido ou planejado nesta sessão.

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

Salve o devtrack em `{NomeProjeto}SecondBrain/devtrack/YYYY-MM-DD - {Título}.md`.

Se não encontrar o vault na raiz, procure no diretório pai ou pergunte ao usuário onde está o SecondBrain do projeto.

---

## Passo 5 — Confirmar

Após salvar, exiba:

```
✓ Devtrack salvo: {NomeProjeto}SecondBrain/devtrack/YYYY-MM-DD - {Título}.md

{Se houver pendências abertas}:
Pendências registradas:
- {lista dos checkboxes não marcados}
```

Não mostre o conteúdo completo do devtrack — o usuário pode abrir no Obsidian.
