# secondbrain

Suite de 17 skills para Claude Code que cria e mantém um sistema de memória persistente, documentação e rastreamento de conhecimento para projetos de software.

## O que é

O **SecondBrain** é uma camada de conhecimento viva que cresce junto com o projeto. A cada sessão, o Claude sabe exatamente onde o projeto parou, quais decisões foram tomadas e o que está em aberto — sem precisar reexplicar nada.

Ele une três camadas:

- **CLAUDE.md** — instruções, stack e regras do projeto para o Claude Code
- **Vault Obsidian** — documentação local legível por humanos (`{Projeto}SecondBrain/`)
- **Memória Claude Code** — contexto persistente entre sessões (`~/.claude/projects/.../memory/`)

O vault fica no `.gitignore` — é documentação pessoal de cada dev, não vai para o repositório do projeto.

---

## Mascote

Cada skill exibe um cérebro animado em roxo ao ser invocada — partículas ciano e sparks amarelas orbitando por ~2 segundos antes de executar.

Requer Python 3. Fallback estático disponível se Python não estiver instalado.

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

### Análise e diagnóstico

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
├── .gitignore                         ← {Projeto}SecondBrain/ ignorado
└── {Projeto}SecondBrain/              ← vault Obsidian (local, fora do git)
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

E na memória local do Claude Code:

```
~/.claude/projects/{projeto}/memory/
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
│   ├── secondbrain-rfc/
│   └── secondbrain-release/
├── scripts/
│   └── mascot.py                      ← animação do cérebro
├── references/
│   ├── devtrack-format.md             ← padrão dos logs de sessão
│   └── mascot.md                      ← instruções + fallback estático
├── package.json
└── README.md
```

---

## Licença

MIT
