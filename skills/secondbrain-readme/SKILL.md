---
name: secondbrain-readme
description: |
  Gera ou atualiza o README.md do projeto usando o contexto já coletado pelo SecondBrain
  (stack, estrutura, scripts, descrição, features).
  
  Use esta skill sempre que o usuário pedir para:
  - "/readme"
  - "gera o README"
  - "atualiza o README"
  - "cria a documentação principal"
  - "documenta o projeto"
  - ao finalizar uma versão ou feature importante
---

> **Mascote:** imprima o cérebro de `references/mascot.md` com `/readme` antes de qualquer outra resposta.


# SecondBrain — README

Gera um README.md completo e profissional usando o que o SecondBrain já sabe sobre o projeto.

---

## Passo 1 — Coletar contexto

```bash
# Scripts disponíveis
cat package.json 2>/dev/null | grep -A 20 '"scripts"'

# README atual (se existir — para não perder seções customizadas)
cat README.md 2>/dev/null

# Estrutura do projeto
ls -1 2>/dev/null
```

Leia também:
1. `{NomeProjeto}SecondBrain/{NomeProjeto} — Visão Geral.md` — descrição, stack, como rodar
2. `project_overview.md` da memória — objetivo e contexto
3. Os arquivos de `features/` ou `HUs/` — para listar funcionalidades implementadas (CAs ✅)

---

## Passo 2 — Verificar se já existe README

Se já existir um `README.md`:
- Identifique seções customizadas que não devem ser sobrescritas (ex: badges, screenshots, seções únicas)
- Pergunte ao usuário: "Já existe um README. Quer que eu sobrescreva tudo ou só atualize as seções de stack, instalação e features?"
- Aguarde antes de continuar.

Se não existir, gere direto.

---

## Passo 3 — Gerar o README

```markdown
# {NomeProjeto}

> {Descrição em uma frase — o que faz e para quem.}

{Se houver badges relevantes (CI, versão, licença), adicione aqui. Senão, omita.}

---

## Sobre o projeto

{2-3 parágrafos sobre o que o projeto faz, o problema que resolve e o contexto de uso.
 Baseado na descrição da Visão Geral e na memória do projeto.}

## Stack

{Lista das tecnologias principais com versões, se disponíveis.}

- {Tecnologia} — {papel no projeto}
- {Tecnologia} — {papel no projeto}

## Funcionalidades

{Listar as features com CAs ✅ das specs em features/ ou HUs/.
 Se não houver specs formais, listar as principais funcionalidades inferidas dos devtracks.}

- {Feature 1}
- {Feature 2}

## Pré-requisitos

{O que precisa ter instalado antes de rodar o projeto.
 Inferir a partir da stack — Node.js versão X, Python X, Docker, etc.}

## Instalação

```bash
{Comandos de instalação inferidos do package.json, requirements.txt, README anterior, etc.}
```

## Como rodar

```bash
{Scripts de desenvolvimento detectados no package.json (dev, start) ou equivalente.}
```

{Se houver outros comandos relevantes (testes, build, lint):}

```bash
# Testes
{comando}

# Build
{comando}
```

## Estrutura do projeto

```
{Listar as pastas principais com descrição de 1 linha cada.
 Baseado na exploração do Passo 1 e na Visão Geral do vault.}
```

## Licença

{Detectar do package.json ou de arquivo LICENSE. Se não encontrar, omitir esta seção.}
```

---

## Regras

- **Use o idioma do projeto** (conforme `feedback_language.md`).
- **Não invente informação.** Se não souber a versão do Node, não escreva. Deixe como `{versão}`.
- **Seções ausentes são melhores que seções vazias.** Se não há funcionalidades documentadas, omita a seção.
- **Se o projeto já tem um README com conteúdo único** (screenshots, roadmap, contribuidores), preserve essas seções — só atualize o que o SecondBrain sabe.

---

## Passo 4 — Confirmar e salvar

Mostre o README gerado antes de salvar.
Aguarde aprovação do usuário.
Salve em `README.md` na raiz do projeto.

```
✓ README.md salvo na raiz do projeto.
```
