# Modelos do /setup

Texto longo tirado de `skills/secondbrain-setup/SKILL.md` para economizar contexto: a skill aponta para cada modelo e você o abre só quando for gerar o arquivo correspondente.


## Modelo 1 — Camada 1 — CLAUDE.md

```markdown
# CLAUDE.md — {NomeProjeto}

## 1. Sempre ler a memória antes de começar

Ao iniciar qualquer conversa neste projeto:

1. Leia o índice de memória: `{caminho-da-memória}/MEMORY.md`  
   É um índice — siga os links para os arquivos relevantes à tarefa atual.

2. Leia `{caminho-absoluto}/{NomeProjeto}SecondBrain/ESTADO.md` (retrato curto: onde está, próximo passo, bloqueios).
   Se não existir, leia o devtrack mais recente:  
   `ls {caminho-absoluto}/{NomeProjeto}SecondBrain/devtrack/ | sort | tail -1`

3. O mapa de pastas do vault está em `{NomeProjeto}SecondBrain/_secondbrain.md` — consulte-o antes de criar ou procurar documentos.

## 2. Stack e tecnologias

{Stack respondida, formatada como lista com versões se disponíveis}

## 3. Estrutura do projeto

{Pastas principais encontradas na exploração — só as relevantes, 1 linha cada}

## 4. Documentação

Toda documentação fica no vault: {NomeProjeto}SecondBrain/ (mapa em `_secondbrain.md`)
Estado atual: {NomeProjeto}SecondBrain/ESTADO.md
Logs de sessão: {NomeProjeto}SecondBrain/devtrack/ (formato: YYYY-MM-DD - Título.md)

## 5. Regras de desenvolvimento

{Se o usuário respondeu regras, listar como itens com marcadores.
 Se não respondeu: "Nenhuma regra específica definida no setup."}

## 6. Fluxo de trabalho

1. Ler memória e ESTADO.md (ou devtrack mais recente)
2. Entender o contexto antes de implementar
3. Implementar
4. Atualizar devtrack (e ESTADO.md) ao final da sessão
```


## Modelo 2 — {NomeProjeto} — Visão Geral.md

```markdown
---
data: {data-de-hoje}
---

# {NomeProjeto} — Visão Geral

## O que é

{Descrição em uma frase respondida pelo usuário.}

## Stack técnica

| Tecnologia | Detalhe |
|---|---|
{Stack respondida, uma linha por tecnologia}

## Como rodar

{Detectar em package.json (scripts.dev/start), Makefile ou README.
 Se não encontrar, deixar como placeholder.}

## Estrutura de pastas principais

{Pastas raiz relevantes com descrição de 1 linha cada}

## Estado atual

Setup inicial realizado em {data-de-hoje}.
```


## Modelo 3 — project_overview.md

```markdown
---
name: project-overview
description: Stack, objetivo e contexto geral de {NomeProjeto}
metadata:
  type: project
---

{NomeProjeto}: {descrição em uma frase}.

**Stack:** {stack}
**Modo:** {solo / equipe pequena (2–5) / equipe grande (6+)}
{Se equipe + tracker}: **Issue tracker:** {tracker}

**Why:** Contexto inicial registrado no setup do SecondBrain.
**How to apply:** Usar para entender escopo e propósito antes de qualquer tarefa.
```


## Modelo 4 — feedback_language.md

```markdown
---
name: feedback-language
description: Idioma de comunicação preferido neste projeto
metadata:
  type: feedback
---

Responder e documentar sempre em {idioma escolhido}.

**Why:** Preferência definida pelo usuário no setup inicial.
**How to apply:** Toda resposta, comentário de código e documentação gerada deve estar neste idioma.
```


## Modelo 5 — feedback_rules.md (somente se o usuário respondeu regras)

```markdown
---
name: feedback-rules
description: Regras e convenções de desenvolvimento definidas no setup
metadata:
  type: feedback
---

{Cada regra respondida em negrito, uma por parágrafo}

**Why:** Convenções definidas pelo usuário no setup do projeto.
**How to apply:** Seguir sempre, em qualquer tarefa, sem exceção salvo instrução explícita do usuário.
```


## Modelo 6 — project_tools.md (somente se equipe + issue tracker ≠ "nenhum")

```markdown
---
name: project-tools
description: Ferramentas de colaboração e rastreamento de tarefas da equipe
metadata:
  type: reference
---

**Issue tracker:** {tracker respondido}
**Tamanho da equipe:** {tamanho respondido}

**Why:** Contexto de colaboração registrado no setup.
**How to apply:** Ao discutir tarefas ou bugs, referenciar o tracker correto.
```
