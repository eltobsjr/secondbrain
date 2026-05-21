---
name: secondbrain-context
description: |
  Gera um briefing compacto de início de sessão: estado atual do repositório,
  pendências abertas e próxima ação recomendada. Otimizado para começar a trabalhar
  imediatamente, não para revisar histórico.
  
  Use esta skill sempre que o usuário pedir para:
  - "/context"
  - "me coloca no contexto"
  - "qual é o contexto atual"
  - "por onde eu estava"
  - "o que estava fazendo"
  - "carrega o contexto do projeto"
  - ao iniciar uma nova sessão de trabalho
  
  Diferença do /resume: o /resume é uma revisão histórica completa.
  O /context é um briefing de 30 segundos para começar a trabalhar agora.
---

> **Mascote:** imprima o cérebro de `references/mascot.md` com `/context` antes de qualquer outra resposta.


# SecondBrain — Context

Briefing rápido de início de sessão. Foco em: onde estou, o que está aberto, o que fazer agora.

---

## Passo 1 — Coletar dados em paralelo

```bash
# Estado do repositório
git status --short 2>/dev/null
git branch --show-current 2>/dev/null
git log --oneline -5 2>/dev/null

# Devtrack mais recente
ls *SecondBrain/devtrack/ 2>/dev/null | sort | tail -1
```

Leia:
1. O **devtrack mais recente** — inteiro, focando no `## Status` e `## Próximos passos`
2. O **MEMORY.md** — só o índice, para saber o que existe
3. Qualquer arquivo de memória `project_*.md` relevante para o contexto atual
4. O **CHECKLIST.md** do vault, se existir e tiver itens não marcados

**Não leia devtracks antigos.** O mais recente é suficiente para o briefing.

---

## Passo 2 — Gerar o briefing

Produza um output **compacto**. Máximo de 30 linhas. Sem seções desnecessárias.

```markdown
## Contexto — {NomeProjeto} ({data-de-hoje})

**Branch:** {branch atual}
**Último trabalho:** {título do devtrack mais recente} ({data})

### Em aberto
{Lista dos checkboxes [ ] do devtrack mais recente + CHECKLIST.md.
 Máximo 7 itens. Se tiver mais, agrupe ou priorize.
 Se não houver nenhum: "Nenhuma pendência registrada — pronto para nova tarefa."}

### Repositório
{Só se houver algo relevante:
 - Arquivos modificados não commitados: listar brevemente
 - Branch diferente da main/master: mencionar
 - Se tudo limpo e na branch principal: omitir esta seção inteira}

### Fazer agora
{Uma única ação recomendada, específica e acionável.
 Baseada nas pendências + contexto da memória.
 Não uma lista — force a escolha da prioridade mais alta.}
```

---

## Regras

- **Compacto acima de tudo.** Se cabe em menos linhas, melhor.
- **"Fazer agora" é obrigatório e é sempre um único item.** Se o usuário tiver 5 pendências, escolha a mais urgente ou lógica de sequência.
- **Omita o que não importa.** Repositório limpo na branch certa? Não mencione. Stack técnica? O usuário já sabe.
- **Não substitui o /resume.** Se o usuário precisar de histórico completo ou visão de mais de uma sessão, direcione para `/resume`.
