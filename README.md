# secondbrain

Suite de skills para Claude Code que cria e mantém um sistema de memória persistente para projetos de software.

## O que é

O **SecondBrain** é uma camada de conhecimento viva que cresce junto com o projeto. Ele une três peças:

- **CLAUDE.md** — instruções e regras do projeto para o Claude Code
- **Vault Obsidian** — documentação legível por humanos (`{Projeto}SecondBrain/`)
- **Memória Claude Code** — contexto persistente entre sessões (`~/.claude/projects/.../memory/`)

## Skills incluídas

| Skill | Gatilho | Descrição |
|---|---|---|
| `secondbrain:setup` | `/secondbrain-setup` | Setup inicial: explora o repo, faz perguntas e gera as 3 camadas |
| `secondbrain:devtrack` | `/devtrack` | Gera log de sessão em `{Projeto}SecondBrain/devtrack/` |
| `secondbrain:resume` | `/resume` | Resumo do estado atual do projeto + pendências abertas |
| `secondbrain:context` | `/context` | Briefing de início de sessão — o que está em aberto e o que vem a seguir |
| `secondbrain:learn` | `/learn` | Captura um aprendizado/gotcha direto na memória e no vault |
| `secondbrain:decision` | `/decision` | Registra uma decisão técnica com contexto e alternativas |
| `secondbrain:priority` | `/priority` | Atualiza a lista de prioridades em `{Projeto}SecondBrain/prioridade/` |
| `secondbrain:feature` | `/feature` | Cria spec de funcionalidade com critérios de aceitação |
| `secondbrain:audit` | `/audit` | Auditoria de saúde: detecta inconsistências, memórias desatualizadas e tarefas abandonadas |
| `secondbrain:readme` | `/readme` | Gera ou atualiza o README.md a partir do contexto do SecondBrain |
| `secondbrain:standup` | `/standup` | Resumo de daily standup a partir do devtrack mais recente |
| `secondbrain:changelog` | `/changelog` | Gera ou atualiza o CHANGELOG.md no formato Keep a Changelog |
| `secondbrain:onboarding` | `/onboarding` | Guia de onboarding para novos desenvolvedores |
| `secondbrain:postmortem` | `/postmortem` | Post-mortem de incidente com causa raiz e plano de ação |
| `secondbrain:rfc` | `/rfc` | Proposta formal de mudança técnica para discussão em equipe |
| `secondbrain:release` | `/release` | Release notes, CHANGELOG atualizado e tag git |

## Instalação

```bash
claude plugin install https://github.com/eltobsjr/secondbrain
```

Ou manualmente: clone o repositório e aponte o plugin para a pasta local.

## Como usar

Abra o Claude Code dentro de qualquer projeto e rode:

```
/secondbrain-setup
```

O Claude vai explorar o repositório, fazer perguntas de setup e gerar toda a estrutura automaticamente.

Nas sessões seguintes:
- `/devtrack` — ao final de cada sessão de trabalho
- `/resume` — para ver o estado atual antes de começar
- `/context` — para um briefing rápido de início de sessão

## Estrutura do repositório

```
secondbrain/
├── skills/
│   ├── secondbrain-setup/      SKILL.md
│   ├── secondbrain-devtrack/   SKILL.md
│   ├── secondbrain-resume/     SKILL.md
│   ├── secondbrain-context/    SKILL.md
│   ├── secondbrain-learn/      SKILL.md
│   ├── secondbrain-decision/   SKILL.md
│   ├── secondbrain-priority/   SKILL.md
│   ├── secondbrain-feature/    SKILL.md
│   ├── secondbrain-audit/      SKILL.md
│   ├── secondbrain-readme/     SKILL.md
│   ├── secondbrain-standup/    SKILL.md
│   ├── secondbrain-changelog/  SKILL.md
│   ├── secondbrain-onboarding/ SKILL.md
│   ├── secondbrain-postmortem/ SKILL.md
│   ├── secondbrain-rfc/        SKILL.md
│   └── secondbrain-release/    SKILL.md
├── references/
│   └── devtrack-format.md      Padrão de formato dos logs de sessão
├── package.json
└── README.md
```

## Licença

MIT
