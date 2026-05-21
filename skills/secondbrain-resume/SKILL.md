---
name: secondbrain-resume
description: |
  Gera um resumo do estado atual do projeto, com pendências abertas e próximas ações.
  
  Use esta skill sempre que o usuário pedir para:
  - "/resume"
  - "resumo do projeto"
  - "o que está em aberto"
  - "qual o estado atual"
  - "o que foi feito até agora"
  - "me atualiza sobre o projeto"
  - antes de começar uma nova sessão de trabalho
  
  Também útil quando o usuário chega com "por onde eu estava?" ou "o que falta?".
---

> **Mascote:** imprima o cérebro de `references/mascot.md` com `/resume` antes de qualquer outra resposta.


# SecondBrain — Resume

Gera um resumo estruturado do estado atual do projeto.

---

## Passo 1 — Coletar dados

Execute em paralelo:

```bash
# Devtracks mais recentes (últimos 5)
ls {NomeProjeto}SecondBrain/devtrack/ | sort | tail -5

# Git log recente
git log --oneline -10 2>/dev/null

# Status do repositório
git status --short 2>/dev/null
```

Leia:
1. Os **3 devtracks mais recentes** completos — foque nos `## Status` com checkboxes `[ ]` (pendências)
2. O **MEMORY.md** e os arquivos de memória relevantes (`project_overview.md`, qualquer `project_*.md`)
3. O **CHECKLIST.md** do vault, se existir

---

## Passo 2 — Gerar o resumo

Produza o resumo no seguinte formato. Adapte o idioma ao projeto (pt-BR ou en-US conforme `feedback_language.md`).

```markdown
## {NomeProjeto} — Estado atual ({data-de-hoje})

### O que foi feito recentemente
{3-5 bullets com as ações mais significativas dos últimos devtracks.
 Foque em features concluídas, bugs corrigidos, decisões tomadas.
 Não liste cada arquivo modificado — sintetize.}

### Pendências em aberto
{Lista de todos os checkboxes [ ] encontrados nos devtracks recentes e no CHECKLIST.md.
 Agrupe por tema se houver muitas.
 Se não houver pendências, escreva: "Nenhuma pendência registrada."}

### Próxima ação recomendada
{Com base nas pendências e no contexto da memória, qual é a próxima coisa lógica a fazer?
 Uma frase direta, não uma lista.}

### Contexto técnico relevante
{Apenas se houver algo no MEMORY.md que seja crítico para qualquer trabalho futuro —
 ex: uma regra importante, uma pendência de terceiros, um estado parcial de implementação.
 Omitir esta seção se não houver nada urgente.}
```

---

## Regras

- **Seja direto.** O objetivo é orientar o trabalho, não documentar o histórico completo.
- **Pendências abertas são o coração do resume.** Se não tiver nenhuma, diga isso claramente.
- **Não repita o que já está na memória.** Se o usuário já sabe a stack, não liste a stack.
- **Uma próxima ação, não uma lista.** Force a priorização — se tiver 5 pendências, qual vem primeiro?
