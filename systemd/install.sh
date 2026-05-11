#!/usr/bin/env bash
# Install the kb-watch systemd user unit.
set -euo pipefail

SRC="$(dirname "$(readlink -f "$0")")/kb-watch.service"
DEST_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
DEST="$DEST_DIR/kb-watch.service"

mkdir -p "$DEST_DIR" "$HOME/.local/state"
cp "$SRC" "$DEST"

systemctl --user daemon-reload
systemctl --user enable --now kb-watch.service

echo
echo "[kb-watch] installed and started."
echo "  status:   systemctl --user status kb-watch"
echo "  logs:     tail -f ~/.local/state/kb-watch.log"
echo "  stop:     systemctl --user disable --now kb-watch"
