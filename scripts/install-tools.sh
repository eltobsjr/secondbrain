#!/usr/bin/env bash
# Copia as ferramentas do SecondBrain para um caminho estável (~/.local/share/secondbrain/bin),
# que as skills usam como $SB. Rode de novo depois de atualizar o plugin. Não altera nada fora dessa pasta.
# Uso: install-tools.sh [--check]     --check só confere (nada é copiado) e sai com 1 se faltar ou estiver defasado.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
SB="$HOME/.local/share/secondbrain/bin"
FILES="_vault.py xmem.py pend.py semana.py board.py reconcile.py guard_publico.py infer_manifest.py add_frontmatter.py build_index.py gen_estado.py check_vault.py backup.sh install-backup.sh"
VER="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$HERE/../.claude-plugin/plugin.json" 2>/dev/null || echo desconhecida)"

if [ "${1:-}" = "--check" ]; then
  bad=0
  for f in $FILES; do
    [ -f "$HERE/$f" ] || continue
    if [ ! -f "$SB/$f" ]; then echo "falta:      $f"; bad=1
    elif ! cmp -s "$HERE/$f" "$SB/$f"; then echo "defasado:   $f"; bad=1; fi
  done
  inst="$(cat "$SB/VERSION" 2>/dev/null || echo nenhuma)"
  [ "$inst" = "$VER" ] || { echo "versão:     instalada $inst, plugin $VER"; bad=1; }
  if [ -f "$HERE/../gui/secondbrain_gui.py" ] && ! cmp -s "$HERE/../gui/secondbrain_gui.py" "$SB/gui/secondbrain_gui.py" 2>/dev/null; then echo "defasado:   gui/secondbrain_gui.py"; bad=1; fi
  [ "$bad" = 0 ] && echo "ferramentas em dia (versão $VER) em $SB" || echo "rode: bash $HERE/install-tools.sh"
  exit "$bad"
fi

mkdir -p "$SB"
for f in $FILES; do
  [ -f "$HERE/$f" ] && install -m 755 "$HERE/$f" "$SB/$f"
done
echo "$VER" > "$SB/VERSION"
# a unidade do systemd (install-backup.sh) chama esta cópia: se existe, acompanha a versão nova
[ -f "$HOME/.local/share/secondbrain/backup.sh" ] && install -m 755 "$HERE/backup.sh" "$HOME/.local/share/secondbrain/backup.sh"
[ -f "$HERE/../gui/secondbrain_gui.py" ] && mkdir -p "$SB/gui" && cp -r "$HERE/../gui/." "$SB/gui/"
echo "ferramentas instaladas em $SB"

# entrada no menu de aplicativos (só se a interface existir)
if [ -f "$SB/gui/secondbrain_gui.py" ]; then
  APPS="$HOME/.local/share/applications"; mkdir -p "$APPS"
  cat > "$APPS/io.github.eltobsjr.SecondBrain.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=SecondBrain
Comment=Memória cruzada dos seus projetos
Exec=python3 $SB/gui/secondbrain_gui.py
Icon=io.github.eltobsjr.SecondBrain
Terminal=false
Categories=Utility;
StartupWMClass=io.github.eltobsjr.SecondBrain
DESK
  echo "atalho criado: $APPS/io.github.eltobsjr.SecondBrain.desktop"
fi

# ícones do logo (corte pequeno para 16-48 px, normal para o resto)
LOGO="$HERE/../assets/logo"
if [ -f "$LOGO/secondbrain-icon.svg" ]; then
  ICONS="$HOME/.local/share/icons/hicolor"; NAME="io.github.eltobsjr.SecondBrain"
  mkdir -p "$ICONS/scalable/apps"; cp "$LOGO/secondbrain-icon.svg" "$ICONS/scalable/apps/$NAME.svg"
  for n in 16 24 32 48 64 128 256 512; do
    [ -f "$LOGO/secondbrain-icon-$n.png" ] && mkdir -p "$ICONS/${n}x${n}/apps" && cp "$LOGO/secondbrain-icon-$n.png" "$ICONS/${n}x${n}/apps/$NAME.png"
  done
  command -v gtk4-update-icon-cache >/dev/null 2>&1 && gtk4-update-icon-cache -f -t "$ICONS" >/dev/null 2>&1 || true
  echo "ícones instalados em $ICONS"
fi
