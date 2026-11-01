#!/usr/bin/env bash
# Install Amélie into ~/.config/omarchy/themes/amelie with everything the theme
# needs: the palette (unrestricted, so its Lua and terminal files survive), the
# four app hooks, the Lora fonts and the Waterfox generator.
#
# The clone you run this from can live anywhere; the theme is copied into place
# without its .git, which is what keeps Omarchy from treating it as a theme
# installed from a stranger's repo (that path drops Lua, terminal configs and
# vscode.json).

set -euo pipefail

REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
DEST="$CONFIG/omarchy/themes/amelie"
FONT_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/fonts"
BIN_DIR="$HOME/.local/bin"

say() { printf '  %s\n' "$*"; }

if ! command -v omarchy >/dev/null 2>&1; then
  echo "This theme is for Omarchy. Install Omarchy first." >&2
  exit 1
fi

echo "Installing Amélie"
echo

# 1. The theme itself ---------------------------------------------------------
if [[ $REPO != "$DEST" ]]; then
  mkdir -p "$DEST"
  if [[ -e $DEST/.git ]]; then
    # A clone here stages as "from a repo" and loses the files this theme wants
    # to keep. The copy below is the theme's own; the clone stays where it is.
    rm -rf "$DEST/.git"
  fi
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude '.git/' --exclude '.github/' --exclude 'scripts/' \
      --exclude 'hooks/' --exclude 'extras/' \
      "$REPO/" "$DEST/"
  else
    (cd "$REPO" && tar -cf - \
      --exclude='.git' --exclude='.github' --exclude='scripts' \
      --exclude='hooks' --exclude='extras' .) | (cd "$DEST" && tar -xf -)
  fi
  say "theme      $DEST"
else
  say "theme      $REPO (in place)"
fi

# 2. Fonts --------------------------------------------------------------------
install -d "$FONT_DIR"
for font in "$REPO"/fonts/*.ttf; do
  install -m 644 "$font" "$FONT_DIR/$(basename -- "$font")"
done
if command -v fc-cache >/dev/null 2>&1; then
  fc-cache -f "$FONT_DIR" >/dev/null
fi
say "fonts      $FONT_DIR/Lora{,-Italic}.ttf"

# 3. Hooks --------------------------------------------------------------------
for hook in "$REPO"/hooks/theme-set.d/*; do
  omarchy hook install theme-set "$hook" >/dev/null
done
say "hooks      $CONFIG/omarchy/hooks/theme-set.d/"

# 4. Waterfox ----------------------------------------------------------------
install -d "$BIN_DIR"
install -m 755 "$REPO/extras/omarchy-waterfox-theme" "$BIN_DIR/omarchy-waterfox-theme"
say "waterfox   $BIN_DIR/omarchy-waterfox-theme"

# 5. Apply --------------------------------------------------------------------
echo
omarchy theme set amelie
echo
echo "Amélie is applied. The terminal, Neovim, btop, GTK, launcher, notifications"
echo "and lock screen colours come from colors.toml and shell.toml; zed.json,"
echo "warp.yaml and the vencord theme are imported by their apps (see README)."
echo
echo "Update: git -C \"$REPO\" pull && \"$REPO/install.sh\""
