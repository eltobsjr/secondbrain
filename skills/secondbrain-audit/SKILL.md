---
name: secondbrain-audit
description: |
  Audita a saúde do SecondBrain do projeto: detecta memórias desatualizadas,
  tarefas abandonadas, inconsistências entre vault e código, e vault desorganizado.
  Produz um relatório com problemas encontrados e ações sugeridas.
  
  Use esta skill sempre que o usuário pedir para:
  - "/audit"
  - "audita o secondbrain"
  - "verifica a memória do projeto"
  - "o que está desatualizado"
  - "faz uma limpeza da memória"
  - "revisa o vault"
  - após um período longo sem uso do secondbrain
  - quando as respostas do Claude parecerem desconexas com o estado real do projeto
---

> **Mascote:** execute `references/mascot.md` — rode o script `scripts/mascot.py audit` antes de qualquer outra resposta. Se Python não estiver disponível, use o fallback estático do mascot.md.


# SecondBrain — Audit

Verifica a saúde do SecondBrain e identifica o que está desatualizado, inconsistente ou abandonado.

---

## Passo 1 — Coletar tudo

Execute em paralelo:

```bash
# Estrutura do vault
find *SecondBrain/ -type f 2>/dev/null | sort

# Todos os arquivos de memória
ls ~/.claude/projects/$(pwd | sed 's|/|-|g' | sed 's|^-||')/memory/ 2>/dev/null

# Git log recente (para cruzar com devtracks)
git log --oneline --since="30 days ago" 2>/dev/null

# Arquivos do projeto que existem de fato
ls src/ 2>/dev/null || ls app/ 2>/dev/null || ls lib/ 2>/dev/null
```

Leia:
1. **Todos os arquivos de memória** (`~/.claude/projects/.../memory/*.md`)
2. **MEMORY.md** — verifique se cada link aponta para um arquivo que existe
3. **Todos os devtracks** — extraia todos os `- [ ]` e `- [x]` para cruzar
4. **prioridade/atual.md** — se existir
5. **CHECKLIST.md** — se existir

---

## Passo 2 — Executar as verificações

### Verificação 1 — Links quebrados no MEMORY.md

Para cada entrada em `MEMORY.md`, confirme que o arquivo linkado existe na pasta de memória.

**Problema:** `- [Título](arquivo.md)` onde `arquivo.md` não existe.  
**Ação sugerida:** remover a entrada ou recriar o arquivo.

---

### Verificação 2 — Memórias que referenciam caminhos inexistentes

Leia cada `feedback_*.md` e `project_*.md`. Se algum mencionar um caminho de arquivo (ex: `src/themes/rdapp/app/...`), verifique se o arquivo ainda existe:

```bash
# Para cada caminho encontrado nas memórias:
ls {caminho-mencionado} 2>/dev/null || echo "não encontrado"
```

**Problema:** memória descreve uma regra sobre um arquivo que foi movido ou deletado.  
**Ação sugerida:** atualizar a memória com o novo caminho ou remover se irrelevante.

---

### Verificação 3 — Tarefas abandonadas

Cruze os `- [ ]` de todos os devtracks com os `- [x]` dos devtracks mais recentes:

- Item aparece como `[ ]` em devtrack antigo **e** como `[x]` em devtrack recente → concluído, OK
- Item aparece como `[ ]` em devtrack antigo **e** não aparece mais nos recentes → **abandonado**
- Item aparece como `[ ]` repetidamente em múltiplos devtracks sem avançar → **bloqueado ou esquecido**

**Ação sugerida:** para cada item abandonado, decidir: incluir no `prioridade/atual.md`, registrar como `❌ Descartado` na feature correspondente, ou criar um `/decision` explicando por que foi deixado de lado.

---

### Verificação 4 — Devtracks sem padrão

Verifique os arquivos em `devtrack/`:

```bash
ls *SecondBrain/devtrack/ | sort
```

**Problemas a detectar:**
- Arquivos sem data no nome (não seguem `YYYY-MM-DD - Título.md`)
- Arquivos sem seção `## Status`
- Arquivos sem nenhum checkbox `[ ]` ou `[x]`

**Ação sugerida:** listar os arquivos problemáticos para o usuário corrigir manualmente.

---

### Verificação 5 — Memórias redundantes ou conflitantes

Se dois arquivos de memória descrevem a mesma regra ou fato com detalhes diferentes, é um conflito.

Exemplos de conflito:
- `feedback_commit_rules.md` diz "commits em inglês" e `feedback_workflow.md` diz "commits em pt-BR"
- Dois arquivos `project_*.md` descrevem o estado da mesma feature com status diferentes

**Ação sugerida:** mesclar os arquivos conflitantes e manter apenas um.

---

### Verificação 6 — Vault desorganizado

```bash
find *SecondBrain/ -maxdepth 1 -type f -name "*.md" | grep -v "Visão Geral\|CHECKLIST\|ONBOARDING" 2>/dev/null
```

Arquivos `.md` soltos na raiz do vault (que não sejam `Visão Geral`, `CHECKLIST` ou `ONBOARDING`) deveriam estar em subpastas.

**Ação sugerida:** listar os arquivos soltos e sugerir para qual subpasta mover cada um.

---

### Verificação 7 — README desatualizado

```bash
cat README.md 2>/dev/null | head -60
```

Compare o conteúdo do `README.md` com a stack registrada em `project_overview.md` da memória:

- A stack no README bate com a stack na memória?
- A descrição do projeto ainda é precisa?
- Os comandos de instalação/execução ainda existem no `package.json` ou equivalente?

**Problema:** README menciona tecnologia que foi removida, descreve o projeto de forma desatualizada, ou os comandos de `Como rodar` não existem mais.  
**Ação sugerida:** rodar `/readme` para regenerar o README com o contexto atual do SecondBrain.

---

## Passo 3 — Gerar o relatório

```markdown
# Auditoria SecondBrain — {NomeProjeto} ({data-de-hoje})

## Resumo

| Verificação | Status | Problemas |
|---|---|---|
| Links no MEMORY.md | {✅ OK / ⚠️ N problemas} | {N} |
| Caminhos nas memórias | {✅ OK / ⚠️ N problemas} | {N} |
| Tarefas abandonadas | {✅ OK / ⚠️ N problemas} | {N} |
| Padrão dos devtracks | {✅ OK / ⚠️ N problemas} | {N} |
| Memórias conflitantes | {✅ OK / ⚠️ N problemas} | {N} |
| Vault organizado | {✅ OK / ⚠️ N problemas} | {N} |
| README atualizado | {✅ OK / ⚠️ N problemas} | {N} |

{Se tudo OK}: Nenhum problema encontrado. SecondBrain saudável.

---

## Problemas encontrados

{Para cada problema, uma seção:}

### ⚠️ {Nome do problema}
**Onde:** {arquivo ou local específico}
**O que está errado:** {descrição clara}
**Ação sugerida:** {o que fazer para corrigir}
```

---

## Passo 4 — Oferecer correção automática

Após mostrar o relatório, pergunte:

> "Posso corrigir automaticamente os problemas simples? (links quebrados no MEMORY.md, entradas de memória com caminhos desatualizados)"

Se o usuário confirmar, corrija os problemas simples e liste o que foi feito.
Problemas que exigem decisão do usuário (tarefas abandonadas, memórias conflitantes) — liste e aguarde instrução.
