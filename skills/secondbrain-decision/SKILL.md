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
  
  Também PROPOR (e só gravar depois do sim) quando, durante uma conversa técnica, uma decisão importante for tomada
  e o usuário disser "vamos com X então", "decidido: Y", "optamos por Z" —
  mesmo sem pedir explicitamente para registrar.
argument-hint: "[decisão tomada]"
---

# SecondBrain — Decision

> **Vault:** antes de ler ou gravar, resolva o vault e os caminhos conforme `references/vault-resolve.md` (manifesto `_secondbrain.md`; se faltar, migração assistida sem mover nada). Neste arquivo, `{vault}` é a pasta do vault e `{devtrack}`, `{decisoes}`, `{features}`, `{prioridade}` etc. são os caminhos que o manifesto dá a cada papel (sem manifesto, valem os padrões).

Registra decisões técnicas e arquiteturais com contexto suficiente para entendê-las no futuro.

O valor de um decision log não é o que foi decidido — isso está no código.
É o **por quê**: o contexto, as alternativas descartadas, as restrições que existiam naquele momento.

---

## Passo 1 — Capturar a decisão

O conteúdo pode vir de duas formas:

**A) O usuário passou junto com o comando:**
> `/decision usar @Input searchQuery em vez de service porque o componente de lista cria cards dinamicamente`

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

## Passo 2b — Checar substituição e precedentes

Com `$SB` definido (`references/vault-resolve.md`, seção 0):

```bash
python3 -I "${SB:-$HOME/.local/share/secondbrain/bin}/xmem.py" absorb-check "<título e resumo da decisão>" --project <projeto>
python3 -I "${SB:-$HOME/.local/share/secondbrain/bin}/xmem.py" recall "<tema da decisão>" --limit 4
```

- Se uma decisão ativa do projeto vira **obsoleta por inteiro** (3 "sim": mesmo projeto, mesma entidade, substituição integral), a nova leva `substitui: "[[NNN - Título antigo]]"` e a antiga muda **só** o `status` para `substituída por NNN`. Na dúvida, é decisão nova relacionada (`relacionado:`), não substituição. Declare também as outras relações que o `absorb-check` revelar, uma linha cada, só com a concordância do usuário: `estende:` (acrescenta à decisão anterior sem torná-la obsoleta), `contradiz:` (se opõe a outra ainda ativa; fica listada no `/audit` até alguém resolver), `implementa:` (aplica um padrão ou RFC), `referencia:`. Valor: `"[[NNN - Título]]"` no mesmo vault ou `projeto:caminho-sem-.md` entre vaults. O grafo desenha cada tipo com cor e traço próprios.
- Se contradiz outra decisão, use `contradiz:` e avise o usuário.
- Mostre ao usuário os precedentes de outros projetos (🔒 só pelo título) antes de decidir; se a decisão repete um padrão, cite `origem: projeto:nota`.

---

## Passo 3 — Gerar o número da decisão

```bash
ls {vault}/{decisoes}/ 2>/dev/null | grep -oE "^[0-9]+" | sort -n | tail -1
```

Use o **maior número + 1** (a contagem de arquivos quebra com lacunas). Se a pasta não existir, crie-a e comece do 001.
O número é sequencial com 3 dígitos: 001, 002, 003... (respeite `nomes.decisoes` do manifesto).

---

## Passo 4 — Gerar o arquivo

Nome do arquivo: `{NNN} - {Título descritivo}.md`

Exemplos:
- `001 - Propagação de searchQuery via @Input.md`
- `002 - Override de componentes via tema.md`
- `003 - i18n centralizado em pt-BR.json5.md`

Conteúdo:

```markdown
---
tipo: decisao
data: {data-de-hoje}
status: aceita            # proposta | aceita | rejeitada | obsoleta | substituída por NNN
tema: {tema curto, ex.: busca, infraestrutura}
substitui: {NNN, se esta decisão torna outra obsoleta; senão omitir}
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

## Fatores de decisão

{Critérios que pesaram: custo, prazo, risco, restrição de terceiros. Omitir se só havia um fator óbvio.}

## Decisão

**{O que foi decidido, em uma frase direta.}**

{Explicação do porquê essa opção foi escolhida. O que a tornou melhor que as alternativas
 neste contexto específico.}

## Consequências

{Use "Bom, porque…" e "Ruim, porque…" para deixar o trade-off explícito.}

{O que muda com essa decisão. Impactos positivos e negativos.
 Restrições que surgem. O que fica mais fácil e o que fica mais difícil.}

{Se houver pendências ou pontos de revisão futura, liste-os:}
- [ ] {Ponto de revisão, se aplicável}

## Confirmação

{Como saber que a decisão foi cumprida: teste, revisão de código, métrica. Omitir se não se aplica.}
```

> Formato baseado no MADR 4 (contexto, fatores, opções, resultado, consequências, confirmação).

---

## Passo 5 — Salvar no vault

```bash
ls -d *SecondBrain/ 2>/dev/null
```

Salve em `{vault}/{decisoes}/{NNN} - {Título}.md`.

**Decisões não se reescrevem — substituem-se.** Se esta decisão torna outra obsoleta, preencha `substitui:` aqui e, na antiga, mude só o `status` para `substituída por {NNN}` (sem tocar no resto). Se a pasta tiver índice (`README.md` com tabela Nº / Título / Status / Data / Tema), acrescente a linha nova e atualize o status da antiga.

Se a pasta `decisions/` não existir, crie-a.

---

## Passo 6 — Confirmar

```
✓ Decisão registrada: {vault}/{decisoes}/{NNN} - {Título}.md
```

Mostre o conteúdo gerado para o usuário revisar antes de salvar.
Se o usuário quiser ajustar algo, corrija e salve em seguida.
