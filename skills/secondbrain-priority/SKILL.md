---
name: secondbrain-priority
description: |
  Coleta todas as pendências abertas do projeto, consolida e gera uma lista de
  prioridades ordenada em {Projeto}SecondBrain/prioridade/atual.md.
  
  Use esta skill sempre que o usuário pedir para:
  - "/priority"
  - "atualiza as prioridades"
  - "o que está pendente"
  - "me dá uma lista do que falta"
  - "reorganiza as prioridades"
  - "quais são as próximas tarefas"
  - depois de um /resume que revelou muitas pendências espalhadas
  
  Também útil ao final de uma fase grande de trabalho, para consolidar o que sobrou
  antes de começar a próxima.
---

> **Mascote:** execute `references/mascot.md` — rode o script `scripts/mascot.py priority` antes de qualquer outra resposta. Se Python não estiver disponível, use o fallback estático do mascot.md.


# SecondBrain — Priority

Consolida todas as pendências abertas do projeto em uma lista de prioridades única.

O problema que esta skill resolve: pendências ficam espalhadas em vários devtracks,
no CHECKLIST.md e na memória. Esta skill as reúne em um único lugar ordenado.

---

## Passo 1 — Coletar todas as pendências

```bash
# Todos os devtracks (para varrer checkboxes abertos)
ls *SecondBrain/devtrack/ | sort

# Arquivo atual de prioridades (se existir)
cat *SecondBrain/prioridade/atual.md 2>/dev/null
```

Leia:
1. **Todos os devtracks** — extraia cada linha `- [ ] {item}` que aparecer
2. O **CHECKLIST.md** do vault — extraia itens não marcados
3. O **MEMORY.md** — veja se algum arquivo de memória menciona pendências ou próximos passos
4. O `prioridade/atual.md` existente — se houver, use como ponto de partida e atualize

**Dica de busca eficiente:**
```bash
grep -r "- \[ \]" *SecondBrain/devtrack/ 2>/dev/null
grep -r "- \[ \]" *SecondBrain/CHECKLIST.md 2>/dev/null
```

---

## Passo 2 — Deduplicar e consolidar

Muitas pendências aparecem em mais de um devtrack (a mesma tarefa reaparece sessão após sessão). Antes de ordenar:

- **Remova duplicatas** — se o mesmo item aparece em 3 devtracks, mantenha só uma ocorrência
- **Descarte concluídas** — se um item aparece como `- [ ]` em um devtrack antigo mas como `- [x]` em um mais recente, está feito
- **Agrupe por tema** — tarefas relacionadas ao mesmo componente, feature ou área ficam juntas

---

## Passo 3 — Ordenar por prioridade

Ordene os itens consolidados em três níveis:

**Alta** — bloqueante, promessa feita, dependência de outra tarefa, ou explicitamente urgente nos devtracks  
**Média** — importante mas não bloqueante, próxima na sequência lógica  
**Baixa** — nice-to-have, refatoração, melhoria futura, sem prazo

Use o contexto da memória (`project_*.md`) e dos devtracks para inferir prioridade. Se não tiver informação suficiente para decidir, coloque como Média.

---

## Passo 4 — Gerar o arquivo

Salve em `{NomeProjeto}SecondBrain/prioridade/atual.md` (sobrescreva se já existir):

```markdown
---
atualizado: {data-de-hoje}
---

# Prioridades — {NomeProjeto}

## Alta
- [ ] {item mais urgente}
- [ ] {outro item bloqueante}

## Média
- [ ] {item importante, próximo na sequência}
- [ ] {outro item médio}

## Baixa
- [ ] {nice-to-have}
- [ ] {refatoração futura}

---

*Gerado por /priority em {data-de-hoje}. Fontes: {N} devtracks + CHECKLIST.md*
```

---

## Passo 5 — Confirmar

```
✓ {N} pendências encontradas em {N} devtracks
✓ Prioridades salvas: {NomeProjeto}SecondBrain/prioridade/atual.md

Alta: {N} itens
Média: {N} itens
Baixa: {N} itens
```

Mostre o arquivo gerado para o usuário revisar.
Se o usuário quiser reordenar ou reclassificar algum item, ajuste e salve novamente.
