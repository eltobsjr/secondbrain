<p align="center"><img src="assets/logo/secondbrain-icon.svg" width="112" alt="Logo do SecondBrain: um cérebro cuja rede neural é o S do nome, traçado por três nós ligados"></p>

# secondbrain

Suite de 20 skills para Claude Code que cria e mantém um sistema de memória persistente, documentação e rastreamento de conhecimento para projetos de software.

## O que é

O **SecondBrain** é uma camada de conhecimento viva que cresce junto com o projeto. A cada sessão, o Claude sabe exatamente onde o projeto parou, quais decisões foram tomadas e o que está em aberto — sem precisar reexplicar nada.

Ele une três camadas:

- **CLAUDE.md** — instruções, stack e regras do projeto para o Claude Code
- **Vault Obsidian** — documentação local legível por humanos (`{Projeto}SecondBrain/`)
- **Memória Claude Code** — contexto persistente entre sessões (`~/.claude/projects/.../memory/`)

Por padrão o vault fica no `.gitignore` (documentação pessoal de cada dev). Se o projeto preferir versioná-lo junto com o código, o setup pergunta e grava `versionado: true` no manifesto.

---

## Estrutura modular: o manifesto `_secondbrain.md`

Cada projeto tem a estrutura de vault que precisar. As skills **não assumem nomes de pasta**: leem o `_secondbrain.md` na raiz do vault (frontmatter YAML, editável no Obsidian), que mapeia **papéis** (devtrack, decisões, features, prioridade, estado…) para as pastas reais, registra pastas próprias do projeto (`extras`), a convenção de nomes e os campos de frontmatter próprios.

- **Módulos ligáveis**: ative só o que o projeto usa; mude depois com `/secondbrain-setup --estrutura` ou editando o manifesto.
- **Vaults existentes não são refeitos.** Na primeira vez que uma skill roda num vault antigo, ela infere o manifesto a partir do que já existe (`scripts/infer_manifest.py`, dry-run), mostra o plano e só grava o `_secondbrain.md` depois da sua confirmação. Nada é movido, renomeado ou apagado.
- **Pasta nova não é "desorganização"**: o `/audit` valida o vault contra o manifesto dele e oferece registrar o que for novo.
- **`ESTADO.md`**: retrato de uma página, reescrito a cada `/devtrack`, que `/context` lê no lugar do devtrack inteiro.
- **`INDEX.md`**: mapa do vault (tipo, data e título de cada nota), gerado por `scripts/build_index.py` sem modelo e regenerado pelo `/devtrack`. A IA acha o que precisa sem abrir centenas de arquivos.
- **Privacidade**: `sensibilidade: alta` marca vault de startup/institucional (nunca sugerido para versionar). O vault é pessoal; só vai ao git quando o projeto tem equipe, e o `/audit` avisa se uma equipe entrar depois.
- **Backup em HD externo**: `scripts/backup.sh` copia vaults, `CLAUDE.md` e memória para um HD que você marcou (`init`), em cópia simples. **Nunca apaga**: versões antigas vão para `_versoes/`. `scripts/install-backup.sh` instala um gatilho do systemd (sem sudo) que roda o backup ao conectar o HD.
- **Hooks opcionais** (`hooks/`): com `hooks: true` no manifesto, o início da sessão injeta o estado do projeto. Desligados por padrão; sem chamada de modelo.

Detalhes: `references/vault-resolve.md` e `references/manifest-template.md`.

---

## Skills

### Workflow diário

| Comando | O que faz |
|---|---|
| `/secondbrain-setup` | Setup inicial: explora o repo, faz perguntas e gera as 3 camadas. Detecta SecondBrain existente e oferece atualizar em vez de recriar. Flag `--import-history`: importa o histórico de commits (até 50) e gera devtracks retroativos + pasta `commits/` no vault. |
| `/context` | Briefing compacto de início de sessão: branch, último devtrack, pendências abertas e próxima ação recomendada |
| `/devtrack` | Gera o log da sessão em `{Projeto}SecondBrain/devtrack/`. Infere o título automaticamente. Avisa se o último log tem mais de 3 dias. |
| `/standup` | Daily standup em 3 blocos (ontem / hoje / bloqueios) a partir do devtrack mais recente |
| `/resume` | Revisão completa: o que foi feito, todas as pendências abertas e próxima ação recomendada |

### Captura de conhecimento

| Comando | O que faz |
|---|---|
| `/learn` | Captura um aprendizado ou gotcha direto na memória do Claude Code + nota no vault |
| `/decision` | Registra uma decisão técnica com contexto, alternativas consideradas e consequências |

### Gestão de projeto

| Comando | O que faz |
|---|---|
| `/priority` | Coleta todos os `[ ]` dos devtracks e CHECKLIST.md, deduplica e gera `prioridade/atual.md` em Alta / Média / Baixa |
| `/feature` | Cria spec de funcionalidade com critérios de aceitação rastreáveis por emoji (🔲 🔄 ✅ ❌). Sugere `/changelog` quando todos os CAs ficam ✅ |
| `/audit` | 7 verificações de saúde: links quebrados, caminhos inexistentes, tarefas abandonadas, devtracks fora do padrão, memórias conflitantes, vault desorganizado, README desatualizado |

### Documentação

| Comando | O que faz |
|---|---|
| `/readme` | Gera ou atualiza o README.md do projeto usando o contexto do SecondBrain |
| `/changelog` | Gera ou atualiza o CHANGELOG.md no formato Keep a Changelog a partir de devtracks + git log |
| `/onboarding` | Guia completo para novos devs: stack, instalação, padrões, decisões importantes, fluxo de trabalho |
| `/release` | Release notes, CHANGELOG atualizado e tag git (sem auto-push) |
| `/backup` | Backup dos vaults e da memória do Claude Code para HD externo: marca o HD, copia, mostra status e instala o gatilho automático |

### Análise e diagnóstico

| Comando | O que faz |
|---|---|
| `/recall` | **Memória cruzada:** procura em todos os projetos uma solução, decisão ou aprendizado para o problema atual, com política de privacidade por vault |
| `/patterns` | Encontra o que se repete em 2+ projetos e registra o padrão no vault global |

(demais comandos desta seção abaixo)

| Comando | O que faz |
|---|---|
| `/analyze` | Análise completa em 16 dimensões: arquitetura, backend, frontend, banco de dados, segurança, performance, DevOps, qualidade de código, testes, produto e negócio, SEO e acessibilidade. Gera nota geral, top 10 problemas, top 10 pontos fortes e plano de evolução. Salva `PROJECT_CONTEXT.md` na raiz para que o Claude leia automaticamente nas próximas sessões. |
| `/audit` | 7 verificações de saúde: links quebrados, caminhos inexistentes, tarefas abandonadas, devtracks fora do padrão, memórias conflitantes, vault desorganizado, README desatualizado |

### Eventos especiais

| Comando | O que faz |
|---|---|
| `/postmortem` | Post-mortem de incidente: linha do tempo, causa raiz, impacto e plano de ação com dono e prazo |
| `/rfc` | Proposta formal de mudança técnica com alternativas, impacto e pontos em aberto para discussão em equipe |

---

## Memória cruzada, interface nativa e vault global

- **`scripts/xmem.py`**: índice derivado (SQLite + FTS5, sem rede nem modelo) sobre todos os vaults, a memória do Claude Code e os `CLAUDE.md`. Busca híbrida (RRF), arestas tipadas, linhagem de substituição, `recall`, `digest`, `absorb-check`, `patterns`, `dups`, `insights`.
- **Interface nativa** (GTK4 + libadwaita + WebKitGTK): `python3 ~/.local/share/secondbrain/bin/gui/secondbrain_gui.py` ou o atalho "SecondBrain" no menu. Busca, leitor, grafo de todas as notas e pendências.
- **Vault global** `~/GlobalSecondBrain/`: um cartão por projeto (só ponteiros), `padroes/` e `licoes/`.
- **Privacidade:** `crossmem: completo | titulos | nenhum` por vault (padrão `titulos` para `sensibilidade: alta`).
- Instalar as ferramentas: `scripts/install-tools.sh`. Detalhes, qualidade medida e limites: [`docs/ARQUITETURA-MEMORIA-CRUZADA.md`](docs/ARQUITETURA-MEMORIA-CRUZADA.md). Revisão dos `CLAUDE.md`: [`docs/REVISAO-CLAUDE-MD.md`](docs/REVISAO-CLAUDE-MD.md).

---

## Instalação

### Via marketplace (recomendado)

Adicione o repositório como marketplace e instale o plugin:

```
/plugin marketplace add eltobsjr/secondbrain
/plugin install secondbrain@secondbrain
```

### Via linha de comando

```bash
# Adicionar o marketplace
claude plugin marketplace add eltobsjr/secondbrain

# Instalar o plugin
claude plugin install secondbrain@secondbrain
```

### Manualmente (clone local)

```bash
git clone https://github.com/eltobsjr/secondbrain
claude --plugin-dir ./secondbrain
```

Para carregar automaticamente em todas as sessões, adicione ao seu `~/.claude/settings.json`:

```json
{
  "plugins": ["~/.claude/plugins/secondbrain"]
}
```

---

## Como usar

Abra o Claude Code dentro de qualquer projeto e rode:

```
/secondbrain-setup
```

O Claude vai explorar o repositório, fazer perguntas e gerar toda a estrutura automaticamente. Em 2 minutos o projeto está configurado.

### Rotina sugerida

```
Início da sessão  →  /context
Final da sessão   →  /devtrack
Daily standup     →  /standup
Novo aprendizado  →  /learn  "o que descobriu"
Nova decisão      →  /decision
```

---

## O que é gerado no projeto

```
meu-projeto/
├── CLAUDE.md                          ← instruções para o Claude Code
├── PROJECT_CONTEXT.md                 ← contexto gerado pelo /analyze (lido automaticamente pelo Claude)
├── .gitignore                         ← {Projeto}SecondBrain/ ignorado (se versionado: false)
└── {Projeto}SecondBrain/              ← vault Obsidian (estrutura definida pelo manifesto)
    ├── _secondbrain.md                ← manifesto: papéis, pastas próprias, nomes, módulos
    ├── ESTADO.md                      ← retrato curto, reescrito a cada /devtrack
    ├── {Projeto} — Visão Geral.md
    ├── CHECKLIST.md
    ├── devtrack/                      ← logs de sessão (YYYY-MM-DD - Título.md)
    ├── commits/                       ← resumo de cada commit (gerado pelo --import-history)
    ├── prioridade/                    ← atual.md gerado pelo /priority
    ├── análise/                       ← relatórios completos gerados pelo /analyze
    ├── decisions/                     ← ADRs gerados pelo /decision
    ├── features/                      ← specs geradas pelo /feature
    ├── rfcs/                          ← propostas geradas pelo /rfc
    ├── postmortems/                   ← relatórios gerados pelo /postmortem
    └── releases/                      ← release notes do /release
```

Os nomes acima são os padrões; o manifesto pode apontar cada papel para outra pasta e acrescentar pastas próprias (`requisitos/`, `docs/`, `entregas/`…).

E na memória local do Claude Code:

```
~/.claude/projects/{caminho-com-hifens}/memory/   (todo caractere não alfanumérico do caminho vira `-`)
├── MEMORY.md                          ← índice
├── project_overview.md                ← stack e objetivo
├── feedback_language.md               ← idioma de comunicação
├── feedback_rules.md                  ← regras do projeto (se definidas)
└── project_tools.md                   ← issue tracker e equipe (se aplicável)
```

---

## Estrutura do repositório

```
secondbrain/
├── .claude-plugin/
│   ├── plugin.json                    ← manifesto do plugin (nome, versão, autor)
│   └── marketplace.json              ← permite instalar via /plugin marketplace add
├── CLAUDE.md                          ← instruções base para o Claude Code
├── skills/
│   ├── secondbrain-setup/
│   ├── secondbrain-analyze/           ← análise completa + gera PROJECT_CONTEXT.md
│   ├── secondbrain-devtrack/
│   ├── secondbrain-resume/
│   ├── secondbrain-context/
│   ├── secondbrain-learn/
│   ├── secondbrain-decision/
│   ├── secondbrain-priority/
│   ├── secondbrain-feature/
│   ├── secondbrain-audit/
│   ├── secondbrain-readme/
│   ├── secondbrain-standup/
│   ├── secondbrain-changelog/
│   ├── secondbrain-onboarding/
│   ├── secondbrain-postmortem/
│   ├── secondbrain-backup/
│   ├── secondbrain-rfc/
│   └── secondbrain-release/
├── hooks/
│   ├── hooks.json                     ← SessionStart opcional (só age com hooks: true no manifesto)
│   └── session-start.sh
├── docs/                              ← arquitetura da memória cruzada e revisão dos CLAUDE.md
├── gui/                               ← interface nativa (GTK4 + libadwaita)
├── tests/                             ← testes (xmem, interface) e avaliação de qualidade da busca
├── scripts/
│   ├── xmem.py                        ← memória cruzada: índice, busca, recall, digest, absorb-check, patterns
│   ├── install-tools.sh               ← instala ferramentas em ~/.local/share/secondbrain/bin e o atalho do app
│   ├── infer_manifest.py              ← infere o manifesto de um vault existente (dry-run)
│   ├── add_frontmatter.py             ← fase 2: tipo/data nas notas sem frontmatter (aditivo, dry-run)
│   ├── build_index.py                 ← gera o INDEX.md do vault (sem modelo)
│   ├── gen_estado.py                  ← rascunho de ESTADO.md a partir do último devtrack
│   ├── backup.sh                      ← backup para HD externo (só copia, nunca apaga)
│   └── install-backup.sh              ← gatilho automático (systemd do usuário) ao conectar o HD
├── references/
│   ├── vault-resolve.md               ← protocolo comum: manifesto, migração, regras de escrita
│   ├── manifest-template.md           ← modelo do _secondbrain.md
│   ├── estado-format.md               ← formato do ESTADO.md
│   ├── import-history.md              ← --import-history do setup
│   └── devtrack-format.md             ← padrão dos logs de sessão
├── package.json
└── README.md
```

---

## Licença

MIT
