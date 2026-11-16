---
name: secondbrain-changelog
description: |
  Gera ou atualiza o CHANGELOG.md do projeto no formato Keep a Changelog,
  usando os devtracks e git log como fonte.
  
  Use esta skill sempre que o usuário pedir para:
  - "/changelog"
  - "gera o changelog"
  - "atualiza o changelog"
  - "documenta as mudanças da versão"
  - ao preparar um release
  - ao fechar uma versão ou sprint
---

# SecondBrain — Changelog

Gera o CHANGELOG.md no formato [Keep a Changelog](https://keepachangelog.com) usando
devtracks e git log como fonte de verdade.

---

## Passo 1 — Coletar dados

```bash
# CHANGELOG atual (para não perder histórico)
cat CHANGELOG.md 2>/dev/null

# Git log com tags de versão
git log --oneline 2>/dev/null
git tag --sort=-version:refname 2>/dev/null | head -10

# Devtracks (para enriquecer com contexto além dos commits)
ls *SecondBrain/devtrack/ | sort
```

Leia os devtracks desde o último release (ou todos, se não houver release anterior).

---

## Passo 2 — Identificar a versão

Se o projeto usa tags git: use a última tag como versão anterior e pergunte qual é a nova.
Se não usa tags: pergunte qual versão registrar, ou use `Unreleased`.

---

## Passo 3 — Classificar as mudanças

Para cada mudança encontrada nos commits e devtracks, classifique em:

| Categoria | Quando usar |
|---|---|
| `Added` | Nova funcionalidade |
| `Changed` | Mudança em funcionalidade existente |
| `Fixed` | Correção de bug |
| `Removed` | Funcionalidade removida |
| `Security` | Correção de vulnerabilidade |
| `Deprecated` | Funcionalidade marcada para remoção futura |

---

## Passo 4 — Gerar o CHANGELOG

Se já existir um `CHANGELOG.md`, adicione a nova versão no topo e preserve o histórico.
Se não existir, crie do zero.

```markdown
# Changelog

Todas as mudanças notáveis neste projeto estão documentadas aqui.
Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)

## [{versão}] — {data-de-hoje}

### Added
- {Nova funcionalidade em linguagem do usuário final, não técnica}

### Changed
- {O que mudou de comportamento}

### Fixed
- {Bug corrigido, descrito pelo sintoma}

### Removed
- {O que foi removido}

{Omitir seções vazias.}

---

{Histórico anterior preservado abaixo, se existia}
```

---

## Regras

- **Linguagem do usuário final**, não de desenvolvedor. "Botão de mais resultados aparece apenas quando há uma busca ativa" não "Adicionado `@if (searchQuery?.trim())` no template".
- **Omita seções vazias.** Se não há nada removido, não coloque `### Removed`.
- **Use o idioma do projeto** conforme `feedback_language.md`.

---

## Passo 5 — Confirmar e salvar

Mostre o changelog gerado antes de salvar.
Aguarde aprovação do usuário.
Salve em `CHANGELOG.md` na raiz do projeto.

```
✓ CHANGELOG.md salvo/atualizado na raiz do projeto.
```
