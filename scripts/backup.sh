#!/usr/bin/env bash
# SecondBrain — backup dos vaults para HD externo.
#
# Princípios:
#   - SÓ COPIA. Nunca apaga nada no destino (sem --delete). Arquivo alterado na origem tem a
#     versão anterior guardada em _versoes/<data>; arquivo removido na origem continua no backup.
#   - Só escreve em HDs que VOCÊ marcou (arquivo .secondbrain-backup na raiz do HD).
#   - Cópia simples (sem criptografia): quem pegar o HD lê tudo.
#
# Uso:
#   backup.sh init <ponto-de-montagem>   marca um HD como destino de backup
#   backup.sh run [--dry-run] [--force]  copia para todo HD marcado e montado
#   backup.sh auto                       usado pelo systemd ao conectar o HD
#   backup.sh status                     mostra HDs, último backup e fontes
#   backup.sh sources                    lista o que entra no backup
set -u

MARK=".secondbrain-backup"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/secondbrain"
LOG="$STATE/backup.log"
MIN_HOURS="${SECONDBRAIN_BACKUP_MIN_HOURS:-6}"
MAX_SIZE="${SECONDBRAIN_BACKUP_MAX_SIZE:-50M}"
HOST="$(hostname -s)"
mkdir -p "$STATE"

log()    { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG" >&2; }
notify() { command -v notify-send >/dev/null 2>&1 && notify-send -a SecondBrain "$1" "${2:-}" >/dev/null 2>&1 || true; }

# ---------- fontes (caminhos relativos a $HOME) ----------
sources() {
  local v proj
  while IFS= read -r v; do
    [ -f "$v/_secondbrain.md" ] && grep -qE '^backup:[[:space:]]*false' "$v/_secondbrain.md" && continue
    echo "${v#"$HOME"/}"
    proj="$(dirname "$v")"
    [ -f "$proj/CLAUDE.md" ] && echo "${proj#"$HOME"/}/CLAUDE.md"
  done < <(find "$HOME" -maxdepth 6 -type d -name '*SecondBrain' \
            -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.claude/*' \
            -not -path '*/backups-secondbrain/*' 2>/dev/null | sort)
  for d in "$HOME"/.claude/projects/*/memory; do
    [ -d "$d" ] && echo "${d#"$HOME"/}"
  done
}

RSYNC_BASE=(rsync -rtR --safe-links --no-perms --no-owner --no-group
            --exclude=imports/ --exclude=node_modules/ --exclude=.git/ "--max-size=$MAX_SIZE")

# ---------- HDs marcados e montados ----------
marked_drives() {
  local m
  for m in "/run/media/$USER"/* "/media/$USER"/*; do
    [ -d "$m" ] && [ -f "$m/$MARK" ] && mountpoint -q "$m" 2>/dev/null && echo "$m"
  done
  # somente para testes automatizados: pasta comum fazendo papel de HD
  [ -n "${SECONDBRAIN_TEST_DRIVE:-}" ] && [ -f "$SECONDBRAIN_TEST_DRIVE/$MARK" ] && echo "$SECONDBRAIN_TEST_DRIVE"
}

backup_one() {
  local mount="$1" dry="$2" force="$3"
  local dest="$mount/secondbrain-backup/$HOST" stamp; stamp="$(date +%F_%H%M%S)"
  # exFAT/FAT guardam mtime com precisão de 2 s; nos demais sistemas a comparação é exata
  local fst win=0; fst="$(findmnt -no FSTYPE -T "$mount" 2>/dev/null)"
  case "$fst" in vfat|exfat|msdos|fuseblk) win=2;; esac
  RSYNC_BASE+=("--modify-window=$win")
  mkdir -p "$dest/current" || { log "ERRO: não consegui escrever em $dest"; return 1; }

  if [ "$force" = 0 ] && [ -f "$dest/ULTIMO_BACKUP" ]; then
    local age=$(( $(date +%s) - $(stat -c %Y "$dest/ULTIMO_BACKUP") ))
    if [ "$age" -lt $(( MIN_HOURS * 3600 )) ]; then
      log "pulado: último backup em $mount tem $(( age / 60 )) min (mínimo ${MIN_HOURS}h; use --force)"
      return 0
    fi
  fi

  mapfile -t SRC < <(sources)
  [ "${#SRC[@]}" -eq 0 ] && { log "nenhuma fonte encontrada"; return 1; }

  # espaço: estimativa com dry-run
  local need avail
  need=$(cd "$HOME" && "${RSYNC_BASE[@]}" --dry-run --stats --backup "--backup-dir=$dest/_versoes/$stamp" \
          "${SRC[@]}" "$dest/current/" 2>/dev/null | awk -F': ' '/Total transferred file size/{gsub(/[^0-9]/,"",$2); print $2}')
  avail=$(df -B1 --output=avail "$mount" | tail -1 | tr -d ' ')
  if [ -n "$need" ] && [ -n "$avail" ] && [ "$need" -gt "$avail" ]; then
    log "ERRO: espaço insuficiente em $mount (precisa ${need} B, livre ${avail} B)"; notify "Backup SecondBrain falhou" "Espaço insuficiente em $mount"; return 1
  fi

  local extra=(); [ "$dry" = 1 ] && extra=(--dry-run -v)
  log "copiando ${#SRC[@]} fontes para $dest/current$([ "$dry" = 1 ] && echo " (dry-run)")"
  (cd "$HOME" && "${RSYNC_BASE[@]}" --backup "--backup-dir=$dest/_versoes/$stamp" "${extra[@]}" \
      "${SRC[@]}" "$dest/current/") >>"$LOG" 2>&1
  local rc=$?
  if [ $rc -eq 0 ] || [ $rc -eq 24 ]; then
    if [ "$dry" = 0 ]; then
      date '+%F %T' > "$dest/ULTIMO_BACKUP"
      cat > "$dest/LEIAME.txt" <<EOF
Backup do SecondBrain (cópia simples, sem criptografia).
  current/   espelho atual, com os mesmos caminhos relativos a \$HOME (restaurar = copiar de volta)
  _versoes/  versões anteriores de arquivos que mudaram (uma pasta por backup)
Nada é apagado por este backup: arquivos removidos na origem permanecem em current/.
Gerado por secondbrain/scripts/backup.sh
EOF
      log "ok: $mount (${#SRC[@]} fontes)"
      notify "Backup SecondBrain concluído" "$mount"
    fi
    return 0
  fi
  log "ERRO: rsync saiu com código $rc (veja $LOG)"; notify "Backup SecondBrain falhou" "rsync código $rc"; return $rc
}

cmd="${1:-run}"; shift || true
dry=0; force=0
for a in "$@"; do case "$a" in --dry-run) dry=1;; --force) force=1;; esac; done

case "$cmd" in
  init)
    m="${1:-}"; [ -z "$m" ] && { echo "uso: backup.sh init <ponto-de-montagem>"; exit 2; }
    { mountpoint -q "$m" || [ "$m" = "${SECONDBRAIN_TEST_DRIVE:-}" ]; } || { echo "$m não é um ponto de montagem (HD conectado e montado?)"; exit 1; }
    [ -f "$m/$MARK" ] && { echo "já marcado: $m"; exit 0; }
    printf 'criado=%s\nmaquina=%s\n' "$(date '+%F')" "$HOST" > "$m/$MARK" && echo "HD marcado: $m (backups em $m/secondbrain-backup/$HOST)"
    ;;
  sources) sources ;;
  status)
    echo "Fontes ($(sources | wc -l)):"; sources | sed 's/^/  /'
    echo; echo "HDs marcados e montados:"; d=$(marked_drives); [ -z "$d" ] && echo "  (nenhum)" || echo "$d" | sed 's/^/  /'
    while IFS= read -r m; do [ -z "$m" ] && continue; f="$m/secondbrain-backup/$HOST/ULTIMO_BACKUP"; echo "  último em $m: $( [ -f "$f" ] && cat "$f" || echo nunca)"; done <<< "$d"
    echo; echo "Log: $LOG"; tail -5 "$LOG" 2>/dev/null | sed 's/^/  /'
    ;;
  auto)
    sleep 8   # deixa o HD terminar de montar
    exec 9>"$STATE/lock"; flock -n 9 || exit 0
    while IFS= read -r m; do [ -n "$m" ] && backup_one "$m" 0 0; done < <(marked_drives)       # ponto de montagem pode ter espaço
    ;;
  run)
    exec 9>"$STATE/lock"; flock -n 9 || { echo "outro backup em andamento"; exit 0; }
    d=$(marked_drives)
    [ -z "$d" ] && { echo "Nenhum HD marcado e montado. Conecte o HD e rode: backup.sh init /run/media/$USER/<nome-do-HD>"; exit 1; }
    while IFS= read -r m; do [ -n "$m" ] && backup_one "$m" "$dry" "$force"; done <<< "$d"
    ;;
  *) echo "comando desconhecido: $cmd"; exit 2;;
esac
