#!/usr/bin/env bash
# Instala (ou remove) o gatilho automático do backup do SecondBrain: ao conectar um HD
# que VOCÊ marcou com `backup.sh init`, o systemd (do seu usuário, sem sudo) roda o backup.
# Sem HD marcado, nada acontece. Uso: install-backup.sh [install|uninstall|status]
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/share/secondbrain"
UNITS="${SECONDBRAIN_UNIT_DIR:-$HOME/.config/systemd/user}"
cmd="${1:-install}"

write_units() {
  mkdir -p "$UNITS"
  cat > "$UNITS/secondbrain-backup.service" <<EOF
[Unit]
Description=SecondBrain: backup para HD externo marcado

[Service]
Type=oneshot
ExecStart=%h/.local/share/secondbrain/backup.sh auto
Nice=10
IOSchedulingClass=idle
TimeoutStartSec=2h
EOF
  cat > "$UNITS/secondbrain-backup.path" <<EOF
[Unit]
Description=SecondBrain: detectar HD externo conectado

[Path]
PathChanged=/run/media/%u
PathChanged=/media/%u
Unit=secondbrain-backup.service

[Install]
WantedBy=default.target
EOF
}

case "$cmd" in
  install)
    mkdir -p "$BIN"; install -m 755 "$HERE/backup.sh" "$BIN/backup.sh"
    write_units
    if [ -z "${SECONDBRAIN_UNIT_DIR:-}" ]; then
      systemctl --user daemon-reload
      systemctl --user enable --now secondbrain-backup.path
      echo "instalado. Marque um HD com:  $BIN/backup.sh init /run/media/$USER/<nome-do-HD>"
    else
      echo "unidades geradas em $UNITS (modo teste)"
    fi ;;
  uninstall)
    systemctl --user disable --now secondbrain-backup.path 2>/dev/null || true
    rm -f "$UNITS/secondbrain-backup.service" "$UNITS/secondbrain-backup.path"
    systemctl --user daemon-reload
    echo "removido (o script em $BIN e os backups nos HDs foram mantidos)" ;;
  status)
    systemctl --user status secondbrain-backup.path --no-pager 2>&1 | head -8 ;;
  *) echo "uso: install-backup.sh [install|uninstall|status]"; exit 2 ;;
esac
