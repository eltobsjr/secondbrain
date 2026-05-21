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
---

# SecondBrain — Feature

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

## Passo 3 — Detectar a pasta de destino

```bash
ls *SecondBrain/ 2>/dev/null
```

Use a pasta adequada conforme o que existir no vault:
- `features/` → padrão para specs de funcionalidade
- `HUs/` → se o projeto usa nomenclatura de Histórias de Usuário
- `components/` → se for uma spec de componente isolado

Se nenhuma existir, crie `features/`.

---

## Passo 4 — Gerar o número sequencial

```bash
ls *SecondBrain/{pasta}/ 2>/dev/null | grep -E "^[0-9]" | wc -l
```

Número com 3 dígitos: 001, 002, 003...

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
✓ Feature criada: {NomeProjeto}SecondBrain/{pasta}/{NNN} - {Nome}.md

CAs registrados: {N}
```

Mostre o documento gerado para o usuário revisar.
Se quiser ajustar CAs, escopo ou descrição, corrija antes de salvar definitivamente.
