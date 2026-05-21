---
name: secondbrain-setup
description: |
  Configura o SecondBrain completo de um projeto de software: explora o repositório,
  faz perguntas de setup e gera as 3 camadas de documentação + memória persistente.
  
  Use esta skill sempre que o usuário pedir para:
  - "configurar o secondbrain"
  - "setup do projeto"
  - "inicializar a memória do projeto"
  - "criar o vault do projeto"
  - iniciar um projeto novo no Claude Code
  - "/secondbrain-setup"
  
  Não espere que o usuário diga exatamente "secondbrain" — qualquer pedido de
  "organizar a documentação do projeto", "criar estrutura de memória" ou
  "deixar o Claude preparado para este projeto" também deve acionar esta skill.
---

# SecondBrain Setup

Configure a documentação persistente e a memória do Claude Code para este projeto.

**Ordem obrigatória: explorar → perguntar → gerar. Não gere nada antes de concluir as perguntas.**

---

## Passo 1 — Explorar o repositório

Leia os seguintes arquivos (se existirem) e registre o que encontrou:

- `package.json` → nome, scripts (`dev`, `start`, `build`), dependências principais
- `requirements.txt` / `pyproject.toml` → stack Python
- `build.gradle` / `pom.xml` → stack Java/Kotlin
- `pubspec.yaml` → stack Flutter/Dart
- `Cargo.toml` → stack Rust
- `go.mod` → stack Go
- `README.md` → nome do projeto, descrição, propósito
- Estrutura da raiz → monorepo? fullstack separado? só frontend?

Execute `pwd` para obter o caminho absoluto — necessário para criar os arquivos de memória.

---

## Passo 2 — Perguntar

Use `AskUserQuestion` se disponível. Senão, apresente como lista numerada.
Pré-preencha as respostas com o que detectou no Passo 1 — o usuário só confirma ou corrige.

### Perguntas fixas (sempre, nesta ordem)

1. **Idioma** — pt-BR / en-US / outro  
   Pré-preencher: pt-BR se o README estiver em português, en-US caso contrário.

2. **Nome do projeto**  
   Pré-preencher: campo `name` do `package.json` ou nome da pasta raiz.

3. **Descrição em uma frase** — O que faz? Para quem?  
   Pré-preencher: primeira frase útil do README, se disponível.

4. **Stack técnica** — confirmar a detectada ou corrigir  
   Ex: "Next.js 14 + Supabase + Tailwind" ou "Django + PostgreSQL + React"

5. **Trabalha sozinho ou em equipe?**  
   Opções: sozinho / equipe pequena (2–5) / equipe grande (6+)

### Perguntas adaptativas (só se aplicável)

- Se detectou framework de UI no `package.json`:  
  "Usa algum sistema de design? (Tailwind, shadcn/ui, Material UI, Bootstrap...)"

- Se detectou backend, API ou banco:  
  "Qual banco de dados? Usa algum ORM ou query builder?"

- Se detectou `pubspec.yaml` (Flutter):  
  "O app roda em iOS, Android ou ambos?"

- Se respondeu equipe (qualquer tamanho):  
  "Usa algum issue tracker? (GitHub Issues / Linear / Jira / Trello / Notion / nenhum)"

- Para qualquer projeto:  
  "Tem especificações formais de funcionalidades? (user stories, HUs, RFCs, PRDs...)  
   Ou trabalha com tasks mais soltas?"

### Pergunta livre (sempre por último)

> "Tem alguma regra, convenção ou comportamento que o Claude deve SEMPRE seguir neste projeto?  
> Exemplos:
> - 'nunca commitar sem minha permissão explícita'
> - 'sempre escrever commits em inglês no imperativo'
> - 'nunca modificar arquivos fora da pasta src/themes/'
> - 'sempre perguntar antes de refatorar código existente'
> 
> Escreva quantas quiser, ou deixe em branco se não tiver."

---

## Passo 3 — Gerar as 3 camadas

Use o idioma escolhido em **todos** os textos gerados.  
O nome do vault é sempre `{NomeProjeto}SecondBrain` (sem espaço, CamelCase).

### Camada 1 — CLAUDE.md

Crie `CLAUDE.md` na raiz do repositório:

```markdown
# CLAUDE.md — {NomeProjeto}

## 1. Sempre ler a memória antes de começar

Ao iniciar qualquer conversa neste projeto, leia o índice de memória em:

{caminho-da-memória}/MEMORY.md

O MEMORY.md é um índice — siga os links para os arquivos relevantes à tarefa
atual. Isso garante continuidade entre sessões.

## 2. Stack e tecnologias

{Stack respondida, formatada como lista com versões se disponíveis}

## 3. Estrutura do projeto

{Pastas principais encontradas na exploração — só as relevantes, 1 linha cada}

## 4. Documentação

Toda documentação fica no vault: {NomeProjeto}SecondBrain/
Logs de sessão: {NomeProjeto}SecondBrain/devtrack/
Formato dos logs: YYYY-MM-DD - Título.md

## 5. Regras de desenvolvimento

{Se o usuário respondeu regras, listar como itens com marcadores.
 Se não respondeu: "Nenhuma regra específica definida no setup."}

## 6. Fluxo de trabalho

1. Ler memória e devtrack mais recente
2. Entender o contexto antes de implementar
3. Implementar
4. Atualizar devtrack ao final da sessão
```

---

### Camada 2 — Vault Obsidian

Crie a pasta `{NomeProjeto}SecondBrain/` na raiz do repositório.

**`{NomeProjeto} — Visão Geral.md`**
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

**`CHECKLIST.md`**
```markdown
# Checklist — {NomeProjeto}

(vazio — preencher conforme necessário)
```

**Pastas base** (sempre criar com `.gitkeep`):
- `devtrack/`
- `prioridade/`

**Pastas adaptativas** (criar só se aplicável):
- Frontend (React/Vue/Angular/Next/Svelte...): `components/`
- Backend ou API: `api/`
- Flutter/mobile: `telas/`
- User stories / HUs / PRDs formais: `features/` (ou `HUs/` se o usuário usou essa nomenclatura)
- Issue tracker (exceto "nenhum"): `tasks/`

**`.gitignore`** — adicionar ao existente (ou criar):
```
# SecondBrain — Obsidian config
{NomeProjeto}SecondBrain/.obsidian/
{NomeProjeto}SecondBrain/.trash/
```

---

### Camada 3 — Memória do Claude Code

**Calcular o caminho:**
- Pegue o resultado do `pwd`
- Substitua cada `/` por `-`
- Prefixe com `~/.claude/projects/`
- Sufixe com `/memory/`

Exemplo: `/home/user/dev/meu-projeto` → `~/.claude/projects/-home-user-dev-meu-projeto/memory/`

Crie os arquivos abaixo nesse caminho.

---

**`MEMORY.md`**
```markdown
# Memory Index

- [Visão geral do projeto](project_overview.md) — Stack, objetivo e estrutura do {NomeProjeto}
- [Idioma de comunicação](feedback_language.md) — Responder sempre em {idioma escolhido}
{Se o usuário deu regras}: - [Regras e convenções](feedback_rules.md) — Regras definidas no setup inicial
{Se equipe + issue tracker}: - [Ferramentas da equipe](project_tools.md) — Issue tracker e fluxo de colaboração
```

---

**`project_overview.md`**
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

---

**`feedback_language.md`**
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

---

**`feedback_rules.md`** *(somente se o usuário respondeu regras)*
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

---

**`project_tools.md`** *(somente se equipe + issue tracker ≠ "nenhum")*
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

---

## Passo 4 — Resumo final

Após criar todos os arquivos, imprima:

```
✓ CLAUDE.md criado na raiz
✓ {NomeProjeto}SecondBrain/ criado com {N} arquivos
✓ {N} arquivos de memória criados em {caminho-da-memória}
✓ .gitignore atualizado

Próximos passos:
1. Abra o Obsidian e aponte o vault para: {caminho-absoluto}/{NomeProjeto}SecondBrain/
2. A cada sessão de trabalho, use /devtrack para gerar o log em:
   {NomeProjeto}SecondBrain/devtrack/YYYY-MM-DD - Título.md
3. Use /resume para ver o estado atual do projeto a qualquer momento.
4. Para projetos em equipe: adicione CLAUDE.md ao controle de versão.
   A memória (~/.claude/...) é local — cada dev cria a sua.
```
