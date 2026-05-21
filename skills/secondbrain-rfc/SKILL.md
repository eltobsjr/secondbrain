---
name: secondbrain-rfc
description: |
  Cria um documento RFC (Request for Comments) para propor uma mudança técnica significativa
  e estruturar a discussão antes da implementação.
  
  Use esta skill sempre que o usuário pedir para:
  - "/rfc"
  - "cria um RFC"
  - "proposta de mudança técnica"
  - "documenta essa proposta"
  - "quero discutir essa mudança antes de implementar"
  - antes de mudanças arquiteturais, migração de tecnologia, novos padrões de código
  - quando a mudança afeta mais de um dev ou precisa de aprovação
---

> **Mascote:** execute `references/mascot.md` — rode o script `scripts/mascot.py rfc` antes de qualquer outra resposta. Se Python não estiver disponível, use o fallback estático do mascot.md.


# SecondBrain — RFC

Cria uma proposta formal de mudança técnica para revisar e discutir antes de implementar.

RFC é útil quando a mudança é grande o suficiente para merecer discussão antes do código.
Se for algo pequeno e óbvio, use `/decision` para registrar após decidir.

---

## Passo 1 — Capturar a proposta

**A) O usuário passou contexto:**
Use como ponto de partida e expanda.

**B) O usuário só digitou `/rfc`:**

Pergunte:
1. "O que você quer propor? Descreva em uma frase."
2. "Por que essa mudança é necessária agora?"

---

## Passo 2 — Número sequencial

```bash
ls *SecondBrain/rfcs/ 2>/dev/null | wc -l
```

Se a pasta não existir, crie e comece do 001.

---

## Passo 3 — Gerar o documento

Nome do arquivo: `{NNN} - {Título da proposta}.md`

```markdown
---
data: {data-de-hoje}
status: proposta
autor: {inferir do git config user.name ou deixar em branco}
---

# RFC {NNN} — {Título}

## Status

`Proposta` → `Em discussão` → `Aceita` / `Rejeitada`

---

## Motivação

{Por que essa mudança é necessária? Qual problema resolve ou qual oportunidade aproveita?
 Seja concreto — descreva o problema atual com exemplos se possível.}

---

## Proposta

{O que exatamente está sendo proposto? Descreva a solução com detalhes suficientes
 para alguém implementar sem ambiguidade.}

{Se a mudança for técnica, inclua exemplos de código, estrutura de pastas, ou interface
 esperada — o suficiente para tornar a proposta concreta.}

---

## Alternativas consideradas

### Alternativa A — {Nome}
{Descrição. Por que não foi escolhida como proposta principal.}

### Alternativa B — {Nome}
{Descrição. Por que não foi escolhida como proposta principal.}

### Não fazer nada
{O que acontece se a mudança não for implementada. Qual é o custo de manter o status quo.}

---

## Impacto

### O que muda
- {O que será diferente após a implementação}

### O que não muda
- {O que permanece igual — limita o escopo}

### Esforço estimado
{Pequeno (horas) / Médio (dias) / Grande (semanas) — com justificativa breve.}

### Riscos
{O que pode dar errado. Como mitigar.}

---

## Plano de implementação

{Se aceita, como seria implementada? Fases, dependências, ordem de execução.
 Não precisa ser detalhado — é uma visão geral para estimar esforço.}

---

## Perguntas em aberto

{Aspectos da proposta que ainda precisam de decisão ou mais investigação.
 Pode ser preenchido durante a discussão.}

- [ ] {Questão que precisa de resposta antes de implementar}
```

---

## Regras

- **Uma proposta por RFC.** Se precisar propor duas mudanças, crie dois RFCs.
- **Seja específico o suficiente para implementar.** RFC vago não gera discussão útil.
- **Sempre inclua "não fazer nada" como alternativa.** Obriga a justificar por que a mudança vale o custo.
- **Use o idioma do projeto** conforme `feedback_language.md`.

---

## Passo 4 — Confirmar e salvar

Mostre o documento gerado.
Aguarde aprovação do usuário antes de salvar.

```
✓ RFC salvo: {NomeProjeto}SecondBrain/rfcs/{NNN} - {Título}.md
```
