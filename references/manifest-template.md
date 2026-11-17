# Manifesto do vault — `_secondbrain.md`

Fica na raiz do vault. Markdown com frontmatter YAML: abre no Obsidian e pode ser editado à mão. Toda chave é opcional; o que faltar usa o padrão de `references/vault-resolve.md`.

```markdown
---
schema: 2
versionado: false          # true = vault vai para o git (ex.: monorepo com vault dentro)
sensibilidade: normal      # normal | alta (alta = startup/institucional: nunca versionar, atenção no backup)
backup: true               # false = este vault fica fora do backup para HD externo (scripts/backup.sh)
hooks: false               # true = ativa os hooks opcionais do plugin neste projeto
diataxis: false            # true = usa tipo-doc e o aviso no /audit
modulos: [devtrack, decisoes, features, rfcs, prioridade, estado]
papeis:                    # papel -> caminho real dentro do vault
  devtrack: devtrack/
  decisoes: decisions/
  features: features/      # pode ser HUs/ ou docs/hu/
  rfcs: rfcs/
  prioridade: prioridade/atual.md
  estado: ESTADO.md
  indice: INDEX.md         # mapa gerado por scripts/build_index.py (não editar à mão)
  analise: analise/        # relatórios do /analyze
extras:                    # pastas próprias do projeto (respeitadas, nunca "desorganização")
  - { path: requisitos/, descricao: "Requisitos, casos de uso, rastreabilidade" }
  - { path: entregas/,   descricao: "O que saiu para terceiros" }
nomes:                     # convenção de nome por papel
  decisoes: "NNN - Título"
  devtrack: "AAAA-MM-DD - Título"
campos-extra:              # frontmatter próprio do projeto; sempre preservado
  features: [fase, uc, us, rf]
criado: AAAA-MM-DD
migrado-de: legado         # presente só em vaults adaptados
---

# {Projeto} — Manifesto do vault

Mapa humano do vault: o que cada pasta guarda e por quê. Edite livremente; as skills leem o frontmatter acima.
```

## Mudar a estrutura depois

Edite o frontmatter à mão, ou rode `/secondbrain-setup --estrutura`. Renomear uma pasta? Troque o caminho em `papeis`/`extras` — nada mais precisa mudar. Quer um módulo novo? Adicione em `modulos` e em `papeis`.
