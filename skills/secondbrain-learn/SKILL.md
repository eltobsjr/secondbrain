---
name: secondbrain-learn
description: |
  Captura um aprendizado, gotcha ou padrão descoberto durante o trabalho e salva
  simultaneamente na memória persistente do Claude Code e no vault Obsidian do projeto.
  
  Use esta skill sempre que o usuário pedir para:
  - "/learn"
  - "salva isso na memória"
  - "anota isso"
  - "guarda esse aprendizado"
  - "registra esse gotcha"
  - "lembra disso para o futuro"
  - "adiciona isso à memória do projeto"
  
  Também acionar quando o usuário descobre algo surpreendente durante a sessão e diz
  coisas como "nossa, não sabia que X", "cuidado com Y", "descobri que Z" —
  mesmo sem pedir explicitamente para salvar.
argument-hint: "[o que registrar]"
---

# SecondBrain — Learn

> **Vault:** antes de ler ou gravar, resolva o vault e os caminhos conforme `references/vault-resolve.md` (manifesto `_secondbrain.md`; se faltar, migração assistida sem mover nada). Neste arquivo, `{vault}` é a pasta do vault e `{devtrack}`, `{decisoes}`, `{features}`, `{prioridade}` etc. são os caminhos que o manifesto dá a cada papel (sem manifesto, valem os padrões).

Captura um aprendizado e persiste nos dois lugares: memória do Claude Code + vault Obsidian.

---

## Passo 1 — Capturar o aprendizado

O conteúdo pode vir de duas formas:

**A) O usuário passou junto com o comando:**
> `/learn O DSpace exige ENTRY_COMPONENTS e DECLARATIONS para @listableObjectComponent`

Use diretamente o que foi passado.

**B) O usuário só digitou `/learn` sem conteúdo:**

Pergunte de forma direta e simples:
> "O que você quer registrar?"

Aguarde a resposta antes de continuar.

---

## Passo 2 — Classificar o aprendizado

Escolha o tipo que melhor descreve o conteúdo:

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feedback` | Regra de comportamento, gotcha, padrão do projeto, o que fazer/não fazer | "Nunca usar display:none — preferir template vazio" |
| `project` | Fato sobre o estado, arquitetura ou contexto do projeto | "O backend usa discovery.xml para configurar filtros" |
| `reference` | Onde encontrar algo em sistemas externos | "Bugs do pipeline ficam no Linear projeto INGEST" |

Em caso de dúvida entre `feedback` e `project`: se for uma **regra ou padrão de trabalho**, use `feedback`. Se for um **fato sobre como o projeto funciona**, use `project`.

---

## Passo 3 — Gerar o slug

Crie um slug curto em inglês, snake_case, que descreva o aprendizado.

Exemplos:
- `dspace_entry_components_required`
- `modal_view_encapsulation`
- `i18n_merge_workflow`
- `backend_filters_discovery_xml`

O nome do arquivo será: `{tipo}_{slug}.md`

---

## Passo 4 — Calcular o caminho da memória

Use a regra de `references/vault-resolve.md`, seção 5 (todo caractere não alfanumérico do `pwd` vira `-`, não só `/`):

```bash
MEM="$HOME/.claude/projects/$(pwd | sed 's|[^A-Za-z0-9]|-|g')/memory"
```

---

## Passo 4b — Procurar antes de criar (checagem de absorção)

Com `$SB` definido (`references/vault-resolve.md`, seção 0), rode:

```bash
python3 -I "$SB/xmem.py" absorb-check "<texto do aprendizado>" --project <projeto>
```

Ele lista as notas parecidas (no projeto e nos outros) com a classificação provável e avisa se há **segredo** no texto. Siga a regra impressa: **substituir uma nota exige 3 "sim"** (mesmo projeto, mesma entidade, o fato novo torna TODA a antiga obsoleta); na dúvida é RELATED, nunca substituição. Escreva o aprendizado como fato **completo e autossuficiente** (uma frase ou parágrafo curto com contexto), não como lembrete solto. Se veio de outro projeto, registre `origem: projeto:nota` no frontmatter.

**Arestas tipadas (para o grafo e para o `/audit`).** Quando o `absorb-check` mostrar nota parecida, declare a relação no frontmatter da nota nova em vez de deixar só a semelhança automática. Use um dos tipos: `estende: "[[nota]]"` (acrescenta algo à anterior), `contradiz: projeto:caminho` (afirma o oposto; o `/audit` lista as não resolvidas), `implementa:` (aplica uma decisão ou padrão), `referencia:` (apoia-se em) ou `relacionado:`. Valor: `"[[nota]]"` no mesmo vault ou `projeto:caminho-sem-.md` entre vaults. Só use `substitui:` com os 3 "sim". Proponha a relação ao usuário em uma linha e grave só se ele concordar; sem parecida relevante, não invente relação.

Depois, a verificação manual abaixo continua valendo para a memória do Claude:

Leia o `MEMORY.md` e busque nas descrições (e, se preciso, com `grep -ril "{palavras-chave}" "$MEM"`) uma memória sobre o mesmo assunto.

- **Existe e cobre o mesmo ponto** → atualize esse arquivo (acrescente o novo detalhe, ajuste o `description` se mudou) em vez de criar outro. Diga ao usuário qual arquivo foi atualizado.
- **Existe mas contradiz o novo aprendizado** → mostre os dois trechos e pergunte qual vale; não deixe os dois.
- **Não existe** → siga para o Passo 5.

---

## Passo 5 — Criar o arquivo de memória

Crie `{caminho-da-memória}/{tipo}_{slug}.md`:

```markdown
---
name: {slug}
description: {Uma frase que descreve quando este aprendizado é relevante — usada para decidir se deve ser carregado em conversas futuras}
metadata:
  type: {feedback | project | reference}
---

{O aprendizado em linguagem clara e direta. Pode ter 1 parágrafo ou uma lista com bullets.
 Se for uma regra: explique o que fazer E o que não fazer.
 Se for um gotcha: explique o sintoma, a causa e como evitar.}

**Why:** {Por que isso importa — o que acontece se ignorar.}
**How to apply:** {Quando e como aplicar este conhecimento na prática.}
```

Se o aprendizado é um fato que muda (versão, estado, número), escreva a data no texto — `(em AAAA-MM)` — ou aponte para a fonte viva. Se ele se relaciona com outra memória, cite-a com `[[nome-da-memória]]`.

---

## Passo 6 — Atualizar o MEMORY.md

Adicione uma linha ao índice `{caminho-da-memória}/MEMORY.md`:

```markdown
- [{Título curto legível}]({tipo}_{slug}.md) — {mesma descrição de uma frase}
```

Insira na posição adequada — agrupe com outros itens do mesmo tipo (`feedback_*` com feedbacks, `project_*` com projeto).

---

## Passo 7 — Salvar nota no vault (quando o aprendizado for longo ou técnico)

Se o aprendizado tiver mais de 2-3 parágrafos, ou for uma referência técnica detalhada (ex: tabela de comportamentos, diagrama de fluxo, lista de gotchas de um sistema), salve também uma nota no vault:

```bash
ls -d *SecondBrain/ 2>/dev/null  # encontrar o vault
```

Escolha a pasta pelo manifesto (`papeis` e `extras`), não por um padrão fixo:
- Relacionado a uma feature → o papel `features`
- Referência de API, componente, guia ou outra pasta própria do projeto → a entrada de `extras` cuja descrição combina
- Sem pasta que combine → raiz do vault (e, se for recorrente, ofereça criar uma pasta e registrá-la em `extras`)

Nome do arquivo: `{Título descritivo}.md`

Para aprendizados curtos (1-2 frases), **não crie nota no vault** — a memória é suficiente.

---

## Passo 8 — Confirmar

```
✓ Memória salva: {tipo}_{slug}.md
✓ MEMORY.md atualizado
{Se criou nota no vault}: ✓ Nota criada: {vault}/{arquivo}.md
```

Mostre também o conteúdo do arquivo de memória criado para o usuário confirmar que está correto.
