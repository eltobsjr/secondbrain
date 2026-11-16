---
name: secondbrain-feature
description: |
  Cria uma spec de funcionalidade estruturada com critérios de aceitação e rastreamento
  de status por critério. Salva no vault Obsidian do projeto.
  
  Use esta skill sempre que o usuário pedir para:
  - "/feature"
  - "cria uma feature"
  - "documenta essa funcionalidade"
  - "cria spec da feature X"
  - "anota os critérios de aceitação"
  - "cria uma HU"
  - "documenta os requisitos de X"
  - quando for começar a implementar uma funcionalidade nova e quiser registrar o escopo antes
argument-hint: "[nome da feature]"
---

# SecondBrain — Feature

> **Vault:** antes de ler ou gravar, resolva o vault e os caminhos conforme `references/vault-resolve.md` (manifesto `_secondbrain.md`; se faltar, migração assistida sem mover nada). Neste arquivo, `{vault}` é a pasta do vault e `{devtrack}`, `{decisoes}`, `{features}`, `{prioridade}` etc. são os caminhos que o manifesto dá a cada papel (sem manifesto, valem os padrões).

Cria um documento de spec de funcionalidade com critérios de aceitação rastreáveis.

---

## Passo 1 — Capturar o nome da feature

**A) O usuário passou junto com o comando:**
> `/feature DocumentMoreResults — botão de resultados semânticos no card de busca`

Use como título de partida.

**B) O usuário só digitou `/feature`:**

Pergunte:
> "Qual é o nome ou descrição curta da feature?"

---

## Passo 2 — Coletar detalhes (uma pergunta por vez, só se necessário)

Se a conversa já tiver o contexto suficiente, não pergunte. Extraia diretamente.

Caso contrário, pergunte na ordem abaixo, uma de cada vez:

1. "O que esta feature deve fazer? Descreva o comportamento esperado do ponto de vista do usuário."
2. "Quais são os critérios de aceitação? Liste os cenários que precisam funcionar para considerar a feature pronta."
3. "Há alguma restrição técnica, dependência externa ou escopo explicitamente fora?"

---

## Passo 3 — Resolver a pasta de destino

Use o caminho do papel `features` no manifesto (`_secondbrain.md`). Ele pode ser `features/`, `HUs/`, `docs/hu/` ou outro — o projeto manda.
Sem manifesto: `features/` se existir, senão `HUs/` (se o projeto usa Histórias de Usuário), senão crie `features/`.
Se o manifesto tiver `campos-extra.features` (ex.: `fase`, `uc`, `us`, `rf`), inclua esses campos no frontmatter e pergunte os valores.

---

## Passo 4 — Gerar o número sequencial

Use o **maior número existente + 1**, não a contagem de arquivos (a contagem quebra quando há lacunas ou o 000):

```bash
ls {vault}/{features}/ 2>/dev/null | grep -oE "^[0-9]+" | sort -n | tail -1
```

Número com 3 dígitos: 001, 002, 003... (respeite `nomes.features` se o manifesto definir outro padrão).

---

## Passo 5 — Gerar o documento

Nome do arquivo: `{NNN} - {NomeDaFeature}.md`

```markdown
---
data: {data-de-hoje}
status: planejada
---

# {NNN} — {Nome da Feature}

## Objetivo

{O que esta feature entrega para o usuário. Uma ou duas frases diretas.
 Foco no valor, não na implementação.}

## Critérios de aceitação

| # | Critério | Status |
|---|---|---|
| CA01 | {Comportamento esperado, verificável} | 🔲 Pendente |
| CA02 | {Comportamento esperado, verificável} | 🔲 Pendente |
| CA03 | {Comportamento esperado, verificável} | 🔲 Pendente |

{Adicione quantos CAs forem necessários.
 Cada CA deve ser verificável: "o botão aparece quando..." não "funciona bem".}

## Escopo

### Inclui
- {O que está dentro do escopo desta feature}

### Não inclui
{Se houver algo que poderia ser confundido como parte da feature mas não está no escopo.
 Omitir esta seção se não houver ambiguidade.}

## Dependências

{Outras features, sistemas externos, ou trabalho de terceiros necessários antes de implementar.
 Omitir se não houver.}

## Notas técnicas

{Decisões de implementação relevantes, componentes afetados, restrições técnicas.
 Omitir se ainda não houver nada definido — este campo pode ser preenchido durante a implementação.}
```

---

## Passo 6 — Status dos CAs

Os emojis de status são:
- 🔲 Pendente — não implementado
- 🔄 Em progresso — implementação em andamento
- ✅ Concluído — implementado e verificado
- ❌ Descartado — fora do escopo ou cancelado

O usuário atualiza os status conforme implementa. A skill cria tudo como 🔲 Pendente.

---

## Passo 7 — Confirmar

```
✓ Feature criada: {vault}/{features}/{NNN} - {Nome}.md

CAs registrados: {N}
```

Mostre o documento gerado para o usuário revisar.
Se quiser ajustar CAs, escopo ou descrição, corrija antes de salvar definitivamente.

---

## Passo 8 — Detectar feature concluída (ao atualizar status dos CAs)

Quando o usuário atualizar o status dos CAs de uma feature existente e **todos ficarem ✅**,
avise automaticamente:

> "🎉 Todos os CAs da feature '{Nome}' estão concluídos.
> Quer registrar isso no changelog? Posso gerar a entrada agora com `/changelog`."

Não execute o `/changelog` automaticamente — apenas sugira. O usuário decide.
