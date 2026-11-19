#!/usr/bin/env bash
# SecondBrain — hook opcional de SessionStart (desligado por padrão).
# Só age se o vault do projeto tiver `hooks: true` no _secondbrain.md. Não chama modelo, não grava nada,
# não reindexa: injeta um retrato curto (ESTADO + notas relevantes + itens parados), no máximo 1500 caracteres.
dir="${CLAUDE_PROJECT_DIR:-$PWD}"
# acha o vault na pasta atual ou subindo até 5 níveis (projetos abertos numa subpasta), sem nunca subir até a pasta pessoal
manifest=""; d="$dir"
for _ in 1 2 3 4 5 6; do
  m=$(ls "$d"/*SecondBrain/_secondbrain.md 2>/dev/null | head -1)
  if [ -n "$m" ]; then manifest="$m"; break; fi
  d=$(dirname "$d")
  [ "$d" = "/" ] || [ "$d" = "$HOME" ] && break
done
[ -z "$manifest" ] && exit 0
grep -qE '^hooks:[[:space:]]*true' "$manifest" || exit 0

vault=$(dirname "$manifest")
HERE="$(cd "$(dirname "$0")" && pwd)"
XM="$HERE/../scripts/xmem.py"; [ -f "$XM" ] || XM="$HOME/.local/share/secondbrain/bin/xmem.py"
if [ -f "$XM" ] && out=$(timeout 4 python3 -I "$XM" hook-context --cwd "$dir" 2>/dev/null) && [ -n "$out" ]; then
  echo "$out"
  exit 0
fi

# fallback sem índice: último estado/devtrack
estado=$(grep -E '^[[:space:]]+estado:' "$manifest" | head -1 | sed -E 's/^[^:]+:[[:space:]]*//; s/[[:space:]]*#.*//')
devdir=$(grep -E '^[[:space:]]+devtrack:' "$manifest" | head -1 | sed -E 's/^[^:]+:[[:space:]]*//; s/[[:space:]]*#.*//')
estado="${estado:-ESTADO.md}"; devdir="${devdir:-devtrack/}"
# o caminho vem do manifesto: só vale se continuar dentro do vault (sem `..`, sem caminho absoluto, sem link para fora)
dentro() { r=$(realpath -m -- "$vault/$1" 2>/dev/null) && case "$r" in "$(realpath -- "$vault")"/*) return 0 ;; esac; return 1; }
dentro "$estado" || estado="ESTADO.md"
dentro "$devdir" || devdir="devtrack/"
echo "SecondBrain ($(basename "$vault")): contexto do projeto."
if [ -f "$vault/$estado" ] && dentro "$estado"; then
  if head -n 12 "$vault/$estado" | grep -qiE '^origem:[[:space:]]*"?rascunho'; then
    echo "⚠ $estado é um rascunho gerado na migração, não um retrato verificado. Confirme o estado com o usuário e rode /devtrack para reescrevê-lo."
  else
    echo "--- $estado (primeiras linhas) ---"; head -n 25 "$vault/$estado"
  fi
else
  last=$(ls "$vault/$devdir" 2>/dev/null | sort | tail -1)
  [ -n "$last" ] && echo "Último devtrack: $devdir$last (leia para retomar)."
fi
echo "Ao encerrar a sessão, rode /devtrack. Mapa do vault: $(basename "$vault")/_secondbrain.md"
exit 0
