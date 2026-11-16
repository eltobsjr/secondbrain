# SecondBrain — Importar histórico de commits (`--import-history`)

Executado pelo `/secondbrain-setup --import-history`. Grava nos papéis `devtrack` e `commits` do manifesto (padrão `devtrack/` e `commits/`); use `{vault}`, `{devtrack}` e `{commits}` como em `references/vault-resolve.md`.

**Execute este passo somente se `$ARGUMENTS` contiver `--import-history`.**  
Pode ser combinado com o setup normal: `/secondbrain-setup --import-history`.  
Também funciona sozinho num projeto já configurado.

### Verificação do limite

```bash
git log --oneline 2>/dev/null | wc -l
```

Se o projeto tiver **mais de 50 commits**, avise e encerre este passo:

> "⚠️ Este projeto tem {N} commits — o `--import-history` funciona apenas em projetos com até 50 commits para evitar geração excessiva de arquivos. Quer que eu importe apenas os últimos 50?"

Se o usuário confirmar, use `git log --oneline -50`. Caso contrário, encerre o passo.

---

### Coleta do histórico

```bash
# Lista completa: hash curto | timestamp ISO | assunto do commit
git log --pretty=format:"%h|%ad|%s" --date=format:"%Y-%m-%d" 2>/dev/null

# Para cada commit, detalhes de arquivos alterados
git log --pretty=format:"COMMIT:%h|%ad|%an|%s" --date=format:"%Y-%m-%d" \
  --stat --no-merges 2>/dev/null
```

---

### Geração dos arquivos

Para cada commit, gere dois arquivos:

#### A) Devtrack em `{vault}/{devtrack}/`

Nome do arquivo: `{YYYY-MM-DD} - {assunto do commit}.md`

Se dois ou mais commits caírem no mesmo dia, **consolide em um único devtrack** com seção por commit:

```markdown
# {YYYY-MM-DD} — {Assunto do commit principal ou "Múltiplos commits"}

> Devtrack gerado retroativamente via `--import-history`.

## O que foi feito

{Para cada commit do dia, um bloco:}

### `{hash}` — {assunto do commit}
**Autor:** {nome do autor}

{Narrativa inferida a partir das mudanças de arquivos. Explique o "por quê" provável
 com base nos arquivos e no nome do commit — não liste apenas os arquivos.}

---

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `{arquivo}` | {inserção / remoção / modificação — infira o contexto pelo nome} |

## Status

- [x] {commit aplicado ao repositório}
```

#### B) Resumo do commit em `{vault}/{commits}/`

Nome do arquivo: `{hash} — {assunto}.md`

```markdown
# {hash} — {assunto do commit}

**Data:** {YYYY-MM-DD}
**Autor:** {nome}
**Hash completo:** {hash longo}

## O que este commit fez

{2-4 frases explicando o que mudou e por que, inferidas a partir dos arquivos alterados
 e do texto da mensagem de commit. Não copie apenas a lista de arquivos — interprete.}

## Arquivos alterados

| Arquivo | Tipo de mudança | Linhas |
|---------|-----------------|--------|
| `{arquivo}` | adicionado / modificado / removido | +{N} -{N} |
```

---

### Após gerar todos os arquivos

```bash
ls {vault}/{devtrack}/ | wc -l
ls {vault}/{commits}/ | wc -l
```

Exiba o resumo:

```
✓ Histórico importado: {N} commits processados
  → {N} devtracks criados em {vault}/{devtrack}/
  → {N} arquivos de commit em {vault}/{commits}/

  Dica: abra o vault no Obsidian e use a visualização de grafo para ver
  a evolução do projeto ao longo do tempo.
```

