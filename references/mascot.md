# SecondBrain — Mascote

Ao iniciar qualquer skill SecondBrain, execute o script de animação **antes** de
qualquer outra resposta ou ação:

```bash
python3 "$(dirname "$0")/../scripts/mascot.py" {nome-do-comando} 2.2
```

Se o script não for encontrado, tente o caminho da instalação do plugin:

```bash
# Localizar o script no cache de plugins
MASCOT=$(find ~/.claude/plugins -name "mascot.py" -path "*/secondbrain/*" 2>/dev/null | head -1)
[ -n "$MASCOT" ] && python3 "$MASCOT" {nome-do-comando} 2.2
```

## Argumento de comando por skill

Passe o nome do comando sem a barra como primeiro argumento:

| Skill | Comando |
|---|---|
| `/secondbrain-setup` | `secondbrain-setup` |
| `/devtrack` | `devtrack` |
| `/resume` | `resume` |
| `/context` | `context` |
| `/learn` | `learn` |
| `/decision` | `decision` |
| `/priority` | `priority` |
| `/feature` | `feature` |
| `/audit` | `audit` |
| `/readme` | `readme` |
| `/standup` | `standup` |
| `/changelog` | `changelog` |
| `/onboarding` | `onboarding` |
| `/postmortem` | `postmortem` |
| `/rfc` | `rfc` |
| `/release` | `release` |

## O que a animação faz

- Cérebro com dois hemisférios em tons de roxo/magenta
- 8 partículas ciano orbitando ao redor (~2 segundos)
- 4 sparks amarelas em órbita interna mais rápida
- Borda escura com nome do comando centralizado
- Termina com frame estático antes de prosseguir

## Se Python não estiver disponível

Imprima o fallback estático:

```
  ╭──────────────────────────────────────────────╮
  │                                              │
  │    .-''''-.  .-'''-.   .-''''-.  .-'''-.    │
  │   /  .-. .-Y`-Y-. .-. \                     │
  │  | _( o ) |   | ( o )_ |   SecondBrain      │
  │  ||  `---'|   |`---'  ||                     │
  │  ||  ~~~~ \   / ~~~~  ||   /{comando}        │
  │   \  `---./`./-.---.`  /                     │
  │    `-._____|___|_____.-'                     │
  │                                              │
  ╰──────────────────────────────────────────────╯
```
