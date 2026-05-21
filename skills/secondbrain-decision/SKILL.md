---
name: secondbrain-decision
description: |
  Registra uma decisão técnica ou arquitetural tomada durante o projeto, com contexto,
  alternativas consideradas e consequências. Salva no vault Obsidian do projeto.
  
  Use esta skill sempre que o usuário pedir para:
  - "/decision"
  - "registra essa decisão"
  - "documenta essa escolha"
  - "anota por que decidimos X"
  - "cria um ADR"
  - "salva o racional dessa decisão"
  
  Também acionar quando, durante uma conversa técnica, uma decisão importante for tomada
  e o usuário disser "vamos com X então", "decidido: Y", "optamos por Z" —
  mesmo sem pedir explicitamente para registrar.
---

> **Mascote:** imprima o cérebro de `references/mascot.md` com `/decision` antes de qualquer outra resposta.


# SecondBrain — Decision

Registra decisões técnicas e arquiteturais com contexto suficiente para entendê-las no futuro.

O valor de um decision log não é o que foi decidido — isso está no código.
É o **por quê**: o contexto, as alternativas descartadas, as restrições que existiam naquele momento.

---

## Passo 1 — Capturar a decisão

O conteúdo pode vir de duas formas:

**A) O usuário passou junto com o comando:**
> `/decision usar @Input searchQuery em vez de service porque o DSpace cria cards dinamicamente`

Use como ponto de partida e expanda com o contexto da conversa.

**B) O usuário só digitou `/decision` sem conteúdo:**

Pergunte:
> "Qual decisão você quer registrar? Descreva em uma frase o que foi decidido."

Aguarde antes de continuar.

---

## Passo 2 — Coletar contexto adicional (se necessário)

Se a decisão não ficou clara apenas com o que o usuário disse, faça **uma pergunta por vez**:

1. "Qual era o problema ou necessidade que motivou essa decisão?"
2. "Quais alternativas foram consideradas antes de escolher isso?"
3. "Há alguma consequência ou trade-off importante que deve ser registrado?"

Não faça todas as perguntas de uma vez. Se a conversa já contém as respostas, use-as diretamente sem perguntar.

---

## Passo 3 — Gerar o número da decisão

```bash
ls {NomeProjeto}SecondBrain/decisions/ 2>/dev/null | wc -l
```

Se a pasta não existir, crie-a e comece do 001.
O número é sequencial com 3 dígitos: 001, 002, 003...

---

## Passo 4 — Gerar o arquivo

Nome do arquivo: `{NNN} - {Título descritivo}.md`

Exemplos:
- `001 - Propagação de searchQuery via @Input.md`
- `002 - Override de componentes DSpace via tema rdapp.md`
- `003 - i18n centralizado em pt-BR.json5.md`

Conteúdo:

```markdown
---
data: {data-de-hoje}
status: aceita
---

# {NNN} — {Título}

## Contexto

{O que estava acontecendo que tornou essa decisão necessária.
 Qual era o problema, a necessidade ou a restrição.
 2-4 parágrafos ou bullets. Seja específico — evite "precisávamos de uma solução".}

## Alternativas consideradas

### Opção A — {Nome da opção}
{Descrição breve. Por que foi considerada. Por que foi descartada.}

### Opção B — {Nome da opção}
{Descrição breve. Por que foi considerada. Por que foi descartada.}

{Adicionar quantas opções forem relevantes. Se só havia uma opção óbvia, registre isso.}

## Decisão

**{O que foi decidido, em uma frase direta.}**

{Explicação do porquê essa opção foi escolhida. O que a tornou melhor que as alternativas
 neste contexto específico.}

## Consequências

{O que muda com essa decisão. Impactos positivos e negativos.
 Restrições que surgem. O que fica mais fácil e o que fica mais difícil.}

{Se houver pendências ou pontos de revisão futura, liste-os:}
- [ ] {Ponto de revisão, se aplicável}
```

---

## Passo 5 — Salvar no vault

```bash
ls -d *SecondBrain/ 2>/dev/null
```

Salve em `{NomeProjeto}SecondBrain/decisions/{NNN} - {Título}.md`.

Se a pasta `decisions/` não existir, crie-a.

---

## Passo 6 — Confirmar

```
✓ Decisão registrada: {NomeProjeto}SecondBrain/decisions/{NNN} - {Título}.md
```

Mostre o conteúdo gerado para o usuário revisar antes de salvar.
Se o usuário quiser ajustar algo, corrija e salve em seguida.
