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

# SecondBrain — Audit

Verifica a saúde do SecondBrain e identifica o que está desatualizado, inconsistente ou abandonado.

---

## Passo 1 — Coletar tudo

Execute em paralelo:

```bash
# Estrutura do vault
find *SecondBrain/ -type f 2>/dev/null | sort

# Todos os arquivos de memória
ls "$MEM" 2>/dev/null   # $MEM: ver references/vault-resolve.md, seção 5

# Git log recente (para cruzar com devtracks)
git log --oneline --since="30 days ago" 2>/dev/null

# Arquivos do projeto que existem de fato
ls src/ 2>/dev/null || ls app/ 2>/dev/null || ls lib/ 2>/dev/null
```

**Primeiro leia o manifesto** `{vault}/_secondbrain.md`. A auditoria valida o vault **contra o manifesto dele**, não contra uma estrutura fixa. Sem manifesto, avise e ofereça a migração assistida (`references/vault-resolve.md`, seção 3) antes de auditar.

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

Leia cada `feedback_*.md` e `project_*.md`. Se algum mencionar um caminho de arquivo (ex: `src/themes/meu-tema/app/...`), verifique se o arquivo ainda existe:

```bash
# Para cada caminho encontrado nas memórias:
ls {caminho-mencionado} 2>/dev/null || echo "não encontrado"
```

**Problema:** memória descreve uma regra sobre um arquivo que foi movido ou deletado.  
**Ação sugerida:** atualizar a memória com o novo caminho ou remover se irrelevante.

---

### Verificação 3 — Tarefas abandonadas

Com o motor, não cruze à mão: `python3 -I "$SB/xmem.py" board summary` já mostra, por projeto, quantos itens estão **ocultos** (ruído, repetido, superado) e `board show --ocultos` lista cada um com o motivo. Sem o motor, cruze os `- [ ]` de todos os devtracks com os `- [x]` dos mais recentes:

- Item aparece como `[ ]` em devtrack antigo **e** como `[x]` em devtrack recente → concluído, OK
- Item aparece como `[ ]` em devtrack antigo **e** não aparece mais nos recentes → **abandonado**
- Item aparece como `[ ]` repetidamente em múltiplos devtracks sem avançar → **bloqueado ou esquecido**

**Ação sugerida:** para cada item abandonado, decidir: incluir no `prioridade/atual.md`, registrar como `❌ Descartado` na feature correspondente, ou criar um `/decision` explicando por que foi deixado de lado.

---

### Verificação 4 — Devtracks sem padrão

Verifique os arquivos em `{vault}/{devtrack}/` contra `nomes.devtrack` do manifesto (padrão `AAAA-MM-DD - Título.md`):

**Problemas a detectar:**
- Arquivos fora do padrão de nome do projeto
- Arquivos sem nenhum checkbox `[ ]` ou `[x]` (impede extrair pendências)
- Devtrack curto sem `## Status` **não é problema** quando o corpo é de uma sessão pequena; só sinalize se também não tem checkbox

**Ação sugerida:** listar os arquivos para o usuário decidir; nunca renomear sozinho.

---

### Verificação 5 — Memórias redundantes ou conflitantes

Se dois arquivos de memória descrevem a mesma regra ou fato com detalhes diferentes, é um conflito.

Exemplos de conflito:
- `feedback_commit_rules.md` diz "commits em inglês" e `feedback_workflow.md` diz "commits em pt-BR"
- Dois arquivos `project_*.md` descrevem o estado da mesma feature com status diferentes

**Ação sugerida:** mesclar os arquivos conflitantes e manter apenas um.

---

### Verificação 6 — Vault x manifesto

Compare as pastas e arquivos de primeiro nível do vault com `papeis`, `extras` e `modulos` do manifesto:

- Pasta de papel ou de `extras` **que não existe no disco** → manifesto desatualizado.
- Pasta no disco que **não está no manifesto** → **não é erro**: ofereça registrá-la em `extras` (com uma descrição) ou ignorar.
- Módulo ligado sem nenhuma nota há muito tempo → pergunte se deve ser desligado.
- Arquivos `.md` soltos na raiz só importam se o projeto não tiver índice/README que os explique.

**Nunca** sugira mover arquivos para adequá-los a uma estrutura padrão. A estrutura do projeto é a referência.

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

### Verificação 8 — Limites do MEMORY.md

O Claude Code só carrega no início da sessão as **200 primeiras linhas ou 25 KB** do `MEMORY.md`.

```bash
wc -l -c "$MEM/MEMORY.md"
```

**Problema:** acima de 150 linhas ou 20 KB (aviso) / 200 linhas ou 25 KB (cortado). Entradas longas demais também desperdiçam espaço — cada linha deve ter ~150 caracteres.
**Ação sugerida:** encurtar descrições, fundir memórias parecidas, arquivar o que ficou obsoleto.

---

### Verificação 9 — Links e referências

- `[[links]]` do vault e das memórias que apontam para nota inexistente.
- `substitui:` / `status: substituída por NNN` em decisões apontando para decisão inexistente, ou a antiga sem o status atualizado.
- Memórias sem entrada no `MEMORY.md` (órfãs).

**Ação sugerida:** corrigir o link, criar a nota ou remover a referência.

---

### Verificação 10 — Frontmatter e frescor

- Notas dos papéis do manifesto sem frontmatter (`tipo`, `data`): liste em lote e ofereça a **fase 2 da migração** (adicionar frontmatter, dry-run primeiro).
- Fatos que mudam (versões, "estado atual", números) sem data nem ponteiro para fonte viva. Priorize `ESTADO.md`, `Visão Geral` e memórias `project_*`.
- `ESTADO.md` com `atualizado:` mais antigo que o devtrack mais recente.

**Ação sugerida:** datar o fato, apontar a fonte ou removê-lo.

---

### Verificação 11 — Segredos (só se `versionado: true`)

Se o vault vai para o git, procure padrões de segredo nas notas:

```bash
grep -rnEi "(api[_-]?key|secret|token|passw(or)?d|senha)\s*[:=]\s*\S{8,}|-----BEGIN [A-Z ]*PRIVATE KEY|(sk|ghp|glpat)-[A-Za-z0-9_-]{16,}" {vault}/ 2>/dev/null
```

**Problema:** credencial em nota versionada.
**Ação sugerida:** remover, rotacionar a credencial e, se já foi commitada, tratar o histórico. **Nunca** repita o valor encontrado no relatório — mostre só arquivo e linha.

---

### Verificação 12 — Tipo de documento (só se `diataxis: true`)

Notas de papéis de conhecimento (guias, análises, specs, decisões) devem ter `tipo-doc`: `tutorial` (aprender fazendo), `how-to` (resolver uma tarefa), `referencia` (consultar fatos) ou `explicacao` (entender o porquê). Devtrack, commits e prioridade são registros e ficam fora. Sinalize como **aviso** páginas sem `tipo-doc` ou que misturam tipos (ex.: um guia passo a passo com longas seções de justificativa). Nunca bloqueie nem reescreva.

---

### Verificação 13 — Vault privado e equipe nova

Para cada vault com `versionado: false` (ou `sensibilidade: alta`), veja se o projeto ganhou equipe desde o setup:

```bash
git -C {raiz-do-projeto} shortlog -sne HEAD 2>/dev/null | head
```

Se a raiz não for um repositório, procure `.git` nas subpastas imediatas (monorepo interno). Mais de um autor → **aviso**: "este vault está marcado como privado mas o projeto já tem {N} autores no git. Continua privado ou deve ser compartilhado?". Nunca mude `versionado` nem o `.gitignore` sozinho; a decisão é do usuário. Vault com `sensibilidade: alta` nunca deve ser sugerido para versionamento: só informe o fato.

---

### Verificação 14 — Índice, estado e backup

- `INDEX.md` mais antigo que a nota mais recente do vault → peça para rodar `python3 -I "$SB/build_index.py" {vault}`.
- `ESTADO.md` com `origem: rascunho` ou mais antigo que o último devtrack → sugerir `/devtrack` para reescrevê-lo.
- Vault com `backup: true` sem nenhum backup recente (`~/.local/state/secondbrain/backup.log`) → lembrar do `/backup` (só informe; não rode).

---

### Verificação 15 — Integridade de caminhos (script)

Rode `python3 -I "$SB/xmem.py" insights` e veja a seção **Quadro** (cartões órfãos e parados em Fazendo/Bloqueado). Rode também `python3 -I "$SB/check_vault.py" {vault}` (somente leitura). Ele confere: papéis e `extras` do manifesto x pastas reais, `[[links]]` quebrados, frontmatter sem fechamento, caminhos citados no `CLAUDE.md` do projeto que não existem e links/órfãs do `MEMORY.md`. O caso mais grave que ele pega: projeto movido de pasta cujo `CLAUDE.md` ainda manda ler a memória do caminho antigo (a memória nunca é carregada). Para corrigir, aponte o caminho para o diretório de memória atual (`references/vault-resolve.md`, seção 5) — confirme com o usuário se o `CLAUDE.md` for marcado como inviolável. Papel que aponta para arquivo ainda não criado (ex.: `prioridade/atual.md` antes do primeiro `/priority`) é só informativo.

---

### Verificação 16 — Memória cruzada

Com `$SB` definido, rode (somente leitura):

```bash
python3 -I "$SB/xmem.py" insights --period 30d
python3 -I "$SB/xmem.py" dups --min 0.80
```

Rode também `python3 -I "$SB/xmem.py" reconcile <projeto> --json` por projeto com repositório e informe: propostas de fechamento com evidência do git (nível A) e **hashes citados nas notas que não existem em nenhum repositório** (nota errada ou repositório que saiu do disco). Repositório com `.git` que o git não reconhece vem em `avisos`.

Informe: itens em aberto parados há mais de 14 dias por projeto, projetos sem devtrack há mais de 30 dias, **contradições declaradas e não resolvidas** (`contradiz:`) e **duplicatas prováveis** (inclusive entre projetos: pode ser cópia que deve virar padrão em `/patterns`). Nunca mescle nem apague por conta própria; proponha.

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
| Vault x manifesto | {✅ OK / ⚠️ N problemas} | {N} |
| README atualizado | {✅ OK / ⚠️ N problemas} | {N} |
| Limites do MEMORY.md | {✅ OK / ⚠️ N problemas} | {N} |
| Links e referências | {✅ OK / ⚠️ N problemas} | {N} |
| Frontmatter e frescor | {✅ OK / ⚠️ N problemas} | {N} |
| Segredos (se versionado) | {✅ OK / ⚠️ N problemas / — não se aplica} | {N} |
| Tipo de documento (se ligado) | {✅ OK / ⚠️ N avisos / — não se aplica} | {N} |
| Equipe em vault privado | {✅ OK / ⚠️ N avisos} | {N} |
| Índice, estado e backup | {✅ OK / ⚠️ N avisos} | {N} |
| Integridade de caminhos | {✅ OK / ⚠️ N problemas} | {N} |
| Memória cruzada (parados, contradições, duplicatas) | {✅ OK / ⚠️ N avisos} | {N} |

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

## Passo 4 — Oferecer correção

Após o relatório, pergunte:

> "Posso corrigir os problemas simples? (links quebrados no MEMORY.md, caminhos desatualizados nas memórias, registro de pastas novas em `extras`)"

- **Sempre mostre o plano antes de aplicar** (dry-run): arquivo, linha, mudança. Só aplique depois do ok.
- Correções ficam restritas a: índice de memória, links, frontmatter acrescentado (nunca alterado) e `_secondbrain.md`. Não mova, renomeie nem apague notas.
- Problemas que exigem decisão (tarefas abandonadas, memórias conflitantes, segredos) — liste e aguarde instrução.