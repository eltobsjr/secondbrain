#!/usr/bin/env bash
# SecondBrain — hook opcional de SessionStart.
# Desligado por padrão: só age se o vault do projeto tiver `hooks: true` no _secondbrain.md.
# Não chama modelo e nunca escreve nada; apenas injeta um retrato curto como contexto.
dir="${CLAUDE_PROJECT_DIR:-$PWD}"
manifest=$(ls "$dir"/*SecondBrain/_secondbrain.md 2>/dev/null | head -1)
[ -z "$manifest" ] && exit 0
grep -qE '^hooks:[[:space:]]*true' "$manifest" || exit 0

vault=$(dirname "$manifest")
estado=$(grep -E '^[[:space:]]+estado:' "$manifest" | head -1 | sed -E 's/^[^:]+:[[:space:]]*//; s/[[:space:]]*#.*//')
devdir=$(grep -E '^[[:space:]]+devtrack:' "$manifest" | head -1 | sed -E 's/^[^:]+:[[:space:]]*//; s/[[:space:]]*#.*//')
estado="${estado:-ESTADO.md}"; devdir="${devdir:-devtrack/}"

echo "SecondBrain ($(basename "$vault")): contexto do projeto."
if [ -f "$vault/$estado" ]; then
  echo "--- $estado (primeiras linhas) ---"
  head -n 25 "$vault/$estado"
else
  last=$(ls "$vault/$devdir" 2>/dev/null | sort | tail -1)
  [ -n "$last" ] && echo "Último devtrack: $devdir$last (leia para retomar)."
fi
echo "Ao encerrar a sessão, rode /devtrack. Mapa do vault: $(basename "$vault")/_secondbrain.md"
exit 0
