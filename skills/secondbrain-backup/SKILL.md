---
name: secondbrain-backup
description: |
  Faz e gerencia o backup dos vaults SecondBrain (e da memória do Claude Code) para um HD
  externo, em cópia simples e sem apagar nada. Marca o HD, roda o backup, mostra o status e
  instala o gatilho automático ao conectar o HD.

  Use esta skill sempre que o usuário pedir para:
  - "/backup"
  - "faz backup do secondbrain"
  - "copia os vaults para o HD"
  - "marca esse HD para backup"
  - "quando foi o último backup"
  - "instala o backup automático"
argument-hint: "[status | init <HD> | run | instalar]"
disable-model-invocation: true
---

# SecondBrain — Backup

> **Vault:** resolva o vault conforme `references/vault-resolve.md`. Aqui interessam as chaves `backup:` e `sensibilidade:` do manifesto.

Copia todos os vaults, o `CLAUDE.md` dos projetos e a memória do Claude Code (`~/.claude/projects/*/memory`) para um HD externo que o usuário **marcou**. Cópia simples, sem criptografia: quem pegar o HD lê tudo.

## Garantias (diga ao usuário se ele perguntar)

- **Só copia. Nunca apaga** no HD. Arquivo que mudou na origem tem a versão anterior guardada em `_versoes/<data>`; arquivo removido na origem continua em `current/`.
- Só escreve em HD com o arquivo `.secondbrain-backup` na raiz (criado por `init`). Qualquer outro pendrive é ignorado.
- Fora do backup: pastas `imports/`, `node_modules/`, `.git/` e arquivos acima de 50 MB. Vault com `backup: false` no manifesto também fica de fora.

## Passo 1 — Localizar o script

```bash
BK="$HOME/.local/share/secondbrain/backup.sh"
[ -x "$BK" ] || BK="$(find ~/.claude/plugins -name backup.sh -path "*secondbrain*" 2>/dev/null | head -1)"
```

## Passo 2 — Executar conforme o pedido

| Pedido | Comando |
|---|---|
| Ver situação | `"$BK" status` |
| Marcar um HD | `"$BK" init /run/media/$USER/<nome-do-HD>` (o HD precisa estar conectado e montado; confirme o caminho com o usuário antes) |
| Simular | `"$BK" run --dry-run` |
| Copiar agora | `"$BK" run` (use `--force` se o último backup tem menos de 6 h) |
| Gatilho automático | `bash <pasta-do-plugin>/scripts/install-backup.sh install` (confirme antes: instala uma unidade do systemd do usuário, sem sudo; remover: `... uninstall`) |

Se `run` disser que não há HD marcado e montado, oriente: conectar o HD, `init`, repetir.

## Passo 3 — Relatar

Mostre: quantas fontes, o HD usado, o horário do backup e o que o log (`~/.local/state/secondbrain/backup.log`) registrou. Se algum vault tem `sensibilidade: alta`, lembre uma vez que o HD guarda a cópia **sem criptografia**; a decisão é do usuário, não insista.

## Restaurar

`<HD>/secondbrain-backup/<máquina>/current/` espelha os caminhos relativos a `$HOME`. Restaurar é copiar de volta (`rsync -a current/<caminho> ~/<caminho>`). Antes de sobrescrever qualquer coisa existente, mostre o que seria substituído e peça confirmação.
