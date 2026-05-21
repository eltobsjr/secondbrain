---
name: secondbrain-standup
description: |
  Gera um resumo de daily standup a partir do devtrack mais recente: o que foi feito,
  o que será feito hoje e se há bloqueios.
  
  Use esta skill sempre que o usuário pedir para:
  - "/standup"
  - "gera o standup"
  - "resumo pra daily"
  - "o que reportar na daily"
  - "monta o standup de hoje"
  - antes de uma reunião de daily/standup
---

> **Mascote:** imprima o cérebro de `references/mascot.md` com `/standup` antes de qualquer outra resposta.


# SecondBrain — Standup

Gera o texto de daily standup a partir do devtrack mais recente.

---

## Passo 1 — Coletar dados

```bash
# Devtrack mais recente
ls *SecondBrain/devtrack/ | sort | tail -1

# Commits recentes (últimas 24h)
git log --oneline --since="24 hours ago" 2>/dev/null
```

Leia:
1. O **devtrack mais recente** inteiro
2. O `prioridade/atual.md` se existir — para inferir o que vem a seguir

---

## Passo 2 — Gerar o standup

Formato padrão de daily standup em 3 blocos:

```
🗓 Daily — {data-de-hoje}

✅ Ontem
{O que foi concluído, baseado nos [x] do devtrack e nos commits das últimas 24h.
 Bullets curtos, 1 linha cada. Foco no resultado, não nos detalhes técnicos.}

🔜 Hoje
{O que será feito hoje, baseado nos [ ] do devtrack e no prioridade/atual.md.
 Máximo 3 itens — os mais próximos na sequência lógica.}

🚧 Bloqueios
{Qualquer dependência externa, pendência de terceiros ou impedimento mencionado
 nos devtracks recentes. Se não houver: "Nenhum bloqueio."}
```

---

## Regras

- **Curto.** Um standup deve ser lido em 30 segundos. Sem detalhes técnicos.
- **"Hoje" são no máximo 3 itens.** Force a priorização.
- **Linguagem humana.** "Implementei o botão de mais resultados" não "Adicionou `DocumentMoreResultsComponent` ao `imports` do `ItemSearchResultListElementComponent`".
- **Adapte o idioma** conforme `feedback_language.md`.

---

## Passo 3 — Entregar

Mostre o standup gerado direto na conversa, sem salvar arquivo.
O usuário copia e cola onde precisar.
