---
name: secondbrain-release
description: |
  Prepara a documentação de um release: release notes, atualiza o CHANGELOG,
  sugere a versão e cria tag git.
  
  Use esta skill sempre que o usuário pedir para:
  - "/release"
  - "prepara o release"
  - "vamos fazer o release"
  - "fechar a versão"
  - "gera as release notes"
  - "taguear a versão"
  - ao preparar um deploy de produção ou publicação de versão
---

> **Mascote:** execute `references/mascot.md` — rode o script `scripts/mascot.py release` antes de qualquer outra resposta. Se Python não estiver disponível, use o fallback estático do mascot.md.


# SecondBrain — Release

Prepara tudo para um release: release notes, CHANGELOG atualizado e tag git.

---

## Passo 1 — Coletar dados

```bash
# Versão atual
cat package.json 2>/dev/null | grep '"version"'
git tag --sort=-version:refname 2>/dev/null | head -5

# Commits desde o último release
git log $(git describe --tags --abbrev=0 2>/dev/null)..HEAD --oneline 2>/dev/null \
  || git log --oneline 2>/dev/null

# Estado do repositório
git status --short 2>/dev/null
```

Leia também:
1. Os devtracks desde o último release (ou últimos 5 se não houver tag)
2. As features com CAs ✅ em `features/` ou `HUs/` — para destacar o que foi entregue
3. O `CHANGELOG.md` existente — para adicionar a nova versão no topo

---

## Passo 2 — Propor a versão

Com base no [Semantic Versioning](https://semver.org) (MAJOR.MINOR.PATCH):

- **PATCH** (1.0.X) — só correções de bugs, sem nova funcionalidade
- **MINOR** (1.X.0) — nova funcionalidade, sem quebrar compatibilidade
- **MAJOR** (X.0.0) — mudança que quebra compatibilidade ou reescrita significativa

Analise os commits e devtracks e proponha a versão. Explique o critério.
Aguarde confirmação do usuário antes de continuar.

---

## Passo 3 — Gerar as release notes

Salve em `{NomeProjeto}SecondBrain/releases/{versão}.md`:

```markdown
# Release {versão} — {data-de-hoje}

## Destaques

{2-3 bullets com as mudanças mais importantes desta versão.
 Linguagem do usuário final — o que ele ganha, não o que mudou no código.}

## Funcionalidades entregues

{Features com todos os CAs ✅. Uma linha por feature.}

## Correções

{Bugs corrigidos desde o último release. Uma linha por bug, descrito pelo sintoma.}

## Mudanças técnicas

{Mudanças de infra, dependências, configuração — relevantes para devs mas não para usuários finais.
 Omitir se não houver.}

## Breaking changes

{O que pode quebrar para quem usa/integra este projeto. Omitir se não houver.}
```

---

## Passo 4 — Atualizar o CHANGELOG

Adicione a nova versão no topo do `CHANGELOG.md` usando o formato Keep a Changelog.
Preserve o histórico abaixo.

---

## Passo 5 — Criar a tag git

Após confirmação do usuário, execute:

```bash
git tag -a v{versão} -m "Release {versão}"
```

Informe ao usuário:
```
✓ Release notes: {NomeProjeto}SecondBrain/releases/{versão}.md
✓ CHANGELOG.md atualizado
✓ Tag v{versão} criada localmente

Para publicar a tag:
  git push origin v{versão}
```

**Não faça push da tag automaticamente** — aguarde instrução explícita do usuário.
