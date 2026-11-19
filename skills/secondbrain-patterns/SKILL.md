---
name: secondbrain-patterns
description: |
  Consolida padrões que se repetem entre projetos: encontra grupos de decisões, aprendizados e
  análises parecidos em 2 ou mais projetos e ajuda a registrar um padrão único no vault global
  (padroes/), com problema, solução comum, onde se aplica e exceções.

  Use esta skill sempre que o usuário pedir para:
  - "/patterns"
  - "quais padrões se repetem nos meus projetos"
  - "consolida os padrões"
  - "padroniza essa solução entre os projetos"
  - "o que eu faço sempre igual"
argument-hint: "[tema opcional]"
disable-model-invocation: true
---

# SecondBrain — Patterns (padrões entre projetos)

> **Ferramentas:** `$SB` conforme `references/vault-resolve.md`, seção 0. Vault global: `~/GlobalSecondBrain/` (se não existir: `python3 -I "${SB:-$HOME/.local/share/secondbrain/bin}/xmem.py" global-init`).

## Passo 1 — Levantar candidatos

```bash
python3 -I "${SB:-$HOME/.local/share/secondbrain/bin}/xmem.py" patterns --min-projects 2 --min-score 0.30
```

Cada candidato é um grupo de notas ativas de **projetos diferentes** que se parecem (decisões, aprendizados, postmortems, análises, features). Mostre ao usuário os candidatos e deixe-o escolher quais merecem virar padrão. Candidato é só proposta: confirme lendo as notas que o compõem.

## Passo 2 — Entender cada padrão escolhido

Leia as notas de origem (as 🔒 só com permissão do usuário). Responda: qual é o problema recorrente? Qual a solução comum? O que difere entre projetos e por quê?

## Passo 3 — Escrever o padrão no vault global

`~/GlobalSecondBrain/padroes/<nome-curto>.md`:

```markdown
---
tipo: padrao
status: ativo
data: {AAAA-MM-DD}
projetos: [a, b]
origem: [projeto:caminho-da-nota, ...]
---

# {Nome do padrão}

## Problema
## Solução comum
## Onde se aplica (e onde não)
## Diferenças entre projetos
## Evidências
{lista de `projeto:nota` com uma linha de contexto; sem copiar trechos de vault 🔒}
```

Regras: um padrão por arquivo; nunca apague um padrão antigo, marque `status: substituído` e use `substitui:`; fatos que mudam levam data.

## Passo 4 — Ligar de volta

Para cada projeto de origem, ofereça acrescentar `padrao: "~/GlobalSecondBrain/padroes/<nome>"` no `ESTADO.md` ou em uma nota de decisão; só com aprovação.

## Passo 5 — Reindexar

```bash
python3 -I "${SB:-$HOME/.local/share/secondbrain/bin}/xmem.py" index
```
