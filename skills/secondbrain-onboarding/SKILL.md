---
name: secondbrain-onboarding
description: |
  Gera um guia de onboarding para novos desenvolvedores do projeto, usando o contexto
  do SecondBrain: stack, padrões, estrutura, regras e como rodar.
  
  Use esta skill sempre que o usuário pedir para:
  - "/onboarding"
  - "cria o guia de onboarding"
  - "documenta como entrar no projeto"
  - "guia para novo dev"
  - "como integrar alguém novo"
  - ao adicionar alguém novo à equipe
---

> **Mascote:** execute `references/mascot.md` — rode o script `scripts/mascot.py onboarding` antes de qualquer outra resposta. Se Python não estiver disponível, use o fallback estático do mascot.md.


# SecondBrain — Onboarding

Gera um guia de onboarding completo para novos desenvolvedores, usando tudo que
o SecondBrain sabe sobre o projeto.

---

## Passo 1 — Coletar contexto

```bash
# Scripts e dependências
cat package.json 2>/dev/null

# Variáveis de ambiente necessárias
cat .env.example 2>/dev/null || cat .env.sample 2>/dev/null
ls .env* 2>/dev/null
```

Leia também:
1. `project_overview.md` da memória — objetivo, stack, modo de trabalho
2. `feedback_rules.md` da memória — regras e convenções do projeto
3. `{NomeProjeto} — Visão Geral.md` do vault — estrutura e como rodar
4. `decisions/` do vault — decisões técnicas importantes que um novo dev precisa entender
5. O CLAUDE.md do projeto — padrões obrigatórios

---

## Passo 2 — Gerar o guia

Salve em `{NomeProjeto}SecondBrain/ONBOARDING.md`:

```markdown
# Onboarding — {NomeProjeto}

> Guia para novos desenvolvedores. Leia do início ao fim antes de começar a codar.

---

## O que é este projeto

{Descrição do projeto: o que faz, para quem, qual o problema que resolve.
 2-3 parágrafos baseados na Visão Geral e na memória.}

## Stack

{Lista das tecnologias com uma linha de contexto sobre o papel de cada uma no projeto.}

---

## Configuração do ambiente

### Pré-requisitos

{O que precisa ter instalado: Node.js X, Python X, Docker, etc.}

### Instalação

```bash
{Passo a passo de instalação, em ordem.}
```

### Variáveis de ambiente

{Se existir .env.example, listar as variáveis e explicar cada uma.
 Indicar quais são obrigatórias e onde obter os valores.
 Se não houver, omitir esta seção.}

### Como rodar

```bash
{Comandos para iniciar o ambiente de desenvolvimento.}
```

---

## Estrutura do projeto

```
{Mapa das pastas principais com descrição de 1 linha.}
```

{Para cada pasta relevante, explique em 1-2 frases o que vai lá e o que não vai.}

---

## Padrões e convenções

{Baseado no CLAUDE.md e no feedback_rules.md. Para cada regra importante:}

### {Nome da regra ou área}
{Explicação de por que a regra existe e como aplicá-la.
 Exemplo prático quando ajudar.}

---

## Decisões técnicas importantes

{Listar as 3-5 decisões mais relevantes do vault decisions/ para um novo dev entender.
 Para cada uma: o que foi decidido e por quê (resumo de 2-3 linhas).}

---

## Fluxo de trabalho

{Como é o dia a dia de desenvolvimento no projeto:
 branches, commits, PRs, revisões, deploys — conforme o que existir na memória.}

---

## Ferramentas do time

{Issue tracker, comunicação, CI/CD, ambientes — conforme project_tools.md.
 Omitir se for projeto solo.}

---

## Onde pedir ajuda

{Canais, pessoas de referência, documentação adicional.
 Se for projeto solo, omitir esta seção.}
```

---

## Regras

- **Escreva para alguém que não conhece o projeto.** Não assuma conhecimento.
- **Seja específico sobre os padrões.** "Siga as convenções do projeto" não ajuda. Diga quais são.
- **Use o idioma do projeto** conforme `feedback_language.md`.
- **Salve no vault**, não na raiz — é documentação interna, não pública.

---

## Passo 3 — Confirmar

Mostre o guia antes de salvar.
Aguarde aprovação do usuário.

```
✓ Onboarding salvo: {NomeProjeto}SecondBrain/ONBOARDING.md
```
