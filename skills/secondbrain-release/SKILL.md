---
name: secondbrain-release
description: |
  Prepara a documentação de um release (release notes, CHANGELOG, versão, tag git) ou só gera/atualiza
  o CHANGELOG.md no formato Keep a Changelog (modo changelog; ex-/changelog).
  
  Use esta skill sempre que o usuário pedir para:
  - "/release" e "/changelog"
  - "gera o changelog" / "atualiza o changelog" / "documenta as mudanças da versão"
  - "prepara o release"
  - "vamos fazer o release"
  - "fechar a versão"
  - "gera as release notes"
  - "taguear a versão"
  - ao preparar um deploy de produção ou publicação de versão
argument-hint: "[changelog | versão]"
---

# SecondBrain — Release

> **Vault:** antes de ler ou gravar, resolva o vault e os caminhos conforme `references/vault-resolve.md` (manifesto `_secondbrain.md`; se faltar, migração assistida sem mover nada). Neste arquivo, `{vault}` é a pasta do vault e `{devtrack}`, `{decisoes}`, `{features}`, `{prioridade}` etc. são os caminhos que o manifesto dá a cada papel (sem manifesto, valem os padrões).

Prepara tudo para um release: release notes, CHANGELOG atualizado e tag git.

**Dois modos.** *Release completo* (pedido de release, versão ou tag): todos os passos. *Só changelog* (pedido de "changelog", "documenta as mudanças"; o antigo `/changelog`): passos 1, 2 e 4, **sem release notes e sem tag**.

**Regra firme:** a tag git só é criada quando o usuário pediu release ou tag **e confirmou**. Pedido só de changelog nunca cria tag. Nada é enviado ao remoto sem instrução explícita.

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

Salve em `{vault}/{releases}/{versão}.md`:

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

## Passo 4 — Atualizar o CHANGELOG (também é o modo "só changelog")

Se não usa tags, pergunte a versão ou use `Unreleased`. Classifique cada mudança dos commits e devtracks (`Added`, `Changed`, `Fixed`, `Removed`, `Security`, `Deprecated`) e adicione a nova versão no topo do `CHANGELOG.md` (Keep a Changelog), preservando o histórico. Se não existe, crie do zero.

```markdown
## [{versão}] — {data-de-hoje}

### Added
- {Nova funcionalidade em linguagem do usuário final}

### Changed
### Fixed
- {Bug descrito pelo sintoma}
```

Regras: linguagem do usuário final ("o botão de mais resultados só aparece quando há uma busca ativa", não "adicionado `@if`"); omita seções vazias; use o idioma do projeto (`feedback_language.md`). **Mostre o changelog e aguarde aprovação antes de salvar.** No modo só changelog, termine aqui: `✓ CHANGELOG.md salvo na raiz`.

---

## Passo 5 — Criar a tag git (só no release completo)

Após confirmação do usuário, execute:

```bash
git tag -a v{versão} -m "Release {versão}"
```

Informe ao usuário:
```
✓ Release notes: {vault}/{releases}/{versão}.md
✓ CHANGELOG.md atualizado
✓ Tag v{versão} criada localmente

Para publicar a tag:
  git push origin v{versão}
```

**Não faça push da tag automaticamente** — aguarde instrução explícita do usuário.
