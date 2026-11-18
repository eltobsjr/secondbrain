---
name: secondbrain-priority
description: |
  Coleta todas as pendências abertas do projeto, consolida e gera uma lista de
  prioridades ordenada em {vault}/{prioridade}.
  
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

# SecondBrain — Priority

> **Vault:** antes de ler ou gravar, resolva o vault e os caminhos conforme `references/vault-resolve.md` (manifesto `_secondbrain.md`; se faltar, migração assistida sem mover nada). Neste arquivo, `{vault}` é a pasta do vault e `{devtrack}`, `{decisoes}`, `{features}`, `{prioridade}` etc. são os caminhos que o manifesto dá a cada papel (sem manifesto, valem os padrões).

Consolida todas as pendências abertas do projeto em uma lista de prioridades única.

**O arquivo gerado é uma visão, não a fonte.** A fonte das pendências é o quadro (`board`); a lista escrita é um retrato dele num dia. Escreva no topo a data e que a lista vem do quadro, e **não** copie para ela itens ocultos (ruído, repetido, superado): eles voltam como pendência velha.

O problema que esta skill resolve: pendências ficam espalhadas em vários devtracks,
no CHECKLIST.md e na memória. Esta skill as reúne em um único lugar ordenado.

---

## Passo 1 — Coletar todas as pendências

> **Se existir o quadro** (`$SB/xmem.py`), comece por ele: `python3 -I "$SB/xmem.py" board show --project <p> --json` já traz os itens deduplicados, com idade e coluna. Grave a ordem com `board move <p> <id> <coluna> --prioridade P1` em vez de reescrever listas. Os passos abaixo valem como fallback sem o motor.

```bash
# Todos os devtracks (para varrer checkboxes abertos)
ls {vault}/{devtrack}/ | sort

# Arquivo atual de prioridades (se existir)
cat {vault}/{prioridade} 2>/dev/null
```

Leia:
1. **Todos os devtracks** — extraia cada linha `- [ ] {item}` que aparecer
2. O **CHECKLIST.md** do vault — extraia itens não marcados
3. O **MEMORY.md** — veja se algum arquivo de memória menciona pendências ou próximos passos
4. O `prioridade/atual.md` existente — se houver, use como ponto de partida e atualize

**Dica de busca eficiente:**
```bash
grep -r "- \[ \]" {vault}/{devtrack}/ 2>/dev/null
grep -r "- \[ \]" {vault}/CHECKLIST.md 2>/dev/null
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

Salve em `{vault}/{prioridade}` (sobrescreva se já existir):

```markdown
---
tipo: prioridade
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
✓ Prioridades salvas: {vault}/{prioridade}

Alta: {N} itens
Média: {N} itens
Baixa: {N} itens
```

Se o vault usa o papel `estado`, atualize também o `ESTADO.md` (seções "Próximo passo" e "Bloqueios", conforme `references/estado-format.md`) e aponte para `{prioridade}` em vez de duplicar a lista.

Mostre o arquivo gerado para o usuário revisar.
Se o usuário quiser reordenar ou reclassificar algum item, ajuste e salve novamente.
