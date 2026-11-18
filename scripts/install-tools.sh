#!/usr/bin/env bash
# Copia as ferramentas do SecondBrain para um caminho estável (~/.local/share/secondbrain/bin),
# que as skills usam como $SB. Rode de novo depois de atualizar o plugin. Não altera nada fora dessa pasta.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
SB="$HOME/.local/share/secondbrain/bin"
mkdir -p "$SB"
for f in _vault.py xmem.py board.py infer_manifest.py add_frontmatter.py build_index.py gen_estado.py check_vault.py backup.sh install-backup.sh; do
  [ -f "$HERE/$f" ] && install -m 755 "$HERE/$f" "$SB/$f"
done
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
