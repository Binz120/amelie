#!/usr/bin/env bash
# Remove what install.sh put on the machine. The theme currently applied is
# switched away first, so the shell is never left pointing at a directory that
# no longer exists.

set -euo pipefail

CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
DEST="$CONFIG/omarchy/themes/amelie"
FONT_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/fonts"
BIN_DIR="$HOME/.local/bin"
HOOK_DIR="$CONFIG/omarchy/hooks/theme-set.d"

HAS_OMARCHY=0
command -v omarchy >/dev/null 2>&1 && HAS_OMARCHY=1

if [[ $HAS_OMARCHY == 1 ]] && [[ $(omarchy theme current 2>/dev/null) == "amelie" ]]; then
  fallback=""
  for candidate in everforest gruvbox catppuccin nord; do
    if omarchy theme list 2>/dev/null | grep -qx "$candidate"; then
      fallback=$candidate
      break
    fi
  done
  if [[ -n $fallback ]]; then
    echo "Switching to $fallback before removing Amélie"
    omarchy theme set "$fallback" || true
  else
    echo "Amélie is still the current theme; set another one before logging out." >&2
  fi
fi

rm -rf "$DEST"
rm -f "$HOOK_DIR/20-waterfox" "$HOOK_DIR/30-fastfetch" \
      "$HOOK_DIR/40-app-configs" "$HOOK_DIR/50-vencord"
rm -f "$BIN_DIR/omarchy-waterfox-theme"
rm -f "$FONT_DIR/Lora-Regular.ttf" "$FONT_DIR/Lora-Italic.ttf"
command -v fc-cache >/dev/null 2>&1 && fc-cache -f "$FONT_DIR" >/dev/null || true

echo "Removed the theme, its hooks, the Lora files it installed and the Waterfox helper."
echo "App configs are untouched: ~/.config/starship.toml and"
echo "$HOME/.config/lazygit/config.yml may still be symlinks into the removed theme —"
echo "delete them if they dangle."
