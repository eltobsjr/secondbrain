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
---

> **Mascote:** execute `references/mascot.md` — rode o script `scripts/mascot.py learn` antes de qualquer outra resposta. Se Python não estiver disponível, use o fallback estático do mascot.md.


# SecondBrain — Learn

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
- `ngbmodal_view_encapsulation`
- `i18n_merge_workflow`
- `backend_filters_discovery_xml`

O nome do arquivo será: `{tipo}_{slug}.md`

---

## Passo 4 — Calcular o caminho da memória

```bash
pwd  # se ainda não souber o caminho absoluto do projeto
```

Caminho da memória: substitua cada `/` por `-` no resultado do pwd, prefixe com `~/.claude/projects/` e sufixe com `/memory/`.

Exemplo: `/home/user/dev/meu-projeto` → `~/.claude/projects/-home-user-dev-meu-projeto/memory/`

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

Salve em `{NomeProjeto}SecondBrain/` na subpasta mais adequada:
- Gotcha ou padrão técnico de um sistema específico → pasta raiz do vault
- Relacionado a um componente/feature → `components/` ou `features/`
- Referência de API ou backend → `api/`

Nome do arquivo: `{Título descritivo}.md`

Para aprendizados curtos (1-2 frases), **não crie nota no vault** — a memória é suficiente.

---

## Passo 8 — Confirmar

```
✓ Memória salva: {tipo}_{slug}.md
✓ MEMORY.md atualizado
{Se criou nota no vault}: ✓ Nota criada: {NomeProjeto}SecondBrain/{arquivo}.md
```

Mostre também o conteúdo do arquivo de memória criado para o usuário confirmar que está correto.
