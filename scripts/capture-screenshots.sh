#!/usr/bin/env bash
# Regenerate the README captures: preview.png and screenshots/*.png.
#
# This opens windows on your desktop, so it is not part of CI. It switches to
# the theme, puts everything on a scratch workspace called `screenshots`, places
# each window by address (never by focus), captures, closes what it opened, and
# puts the previous theme back — including on failure.
#
#   scripts/capture-screenshots.sh            # capture with your current toggles
#   scripts/capture-screenshots.sh --opaque   # hide window glass for the captures
#
# Needs: kitty, btop, lazygit, nvim, flea, grim, jq, wtype, and amélie installed
# as a local theme (install.sh). preview-unlock.png is not captured here: a lock
# screen needs the password to get back, so it is rendered by
# scripts/make-lock-preview.py.

set -euo pipefail

REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
OUT="$REPO/screenshots"
WS="screenshots"

OPAQUE=0
[[ ${1:-} == "--opaque" ]] && OPAQUE=1

for tool in omarchy hyprctl grim jq kitty btop lazygit nvim flea; do
  command -v "$tool" >/dev/null 2>&1 || { echo "missing: $tool" >&2; exit 1; }
done

PREVIOUS_THEME=$(omarchy theme current)

# install.sh installs as `amelie`; a hand-written copy may be `amélie`. Omnarchy
# matches theme names case-insensitively, so either slug works for `theme set`.
TITLE=amelie
if ! omarchy theme list | grep -qix "amelie"; then
  TITLE=$(omarchy theme list | grep -i '^amélie$' || true)
  [[ -n $TITLE ]] || { echo "Amélie is not installed as a theme (run install.sh)" >&2; exit 1; }
fi
PREVIOUS_WORKSPACE=$(hyprctl activeworkspace -j | jq -r '.id')
TOGGLES="$HOME/.local/state/omarchy/toggles/hypr"
GLASS_BACKUP=$(mktemp -u)

cleanup() {
  local status=$?
  for address in $(hyprctl clients -j | jq -r '.[] | select(.class|startswith("shot-")) | .address'); do
    hyprctl dispatch "hl.dsp.window.close({ window = \"address:$address\" })" >/dev/null 2>&1 || true
  done
  for address in $(hyprctl clients -j | jq -r '.[] | select(.class=="com.thisisgm.flea") | .address'); do
    hyprctl dispatch "hl.dsp.window.close({ window = \"address:$address\" })" >/dev/null 2>&1 || true
  done
  omarchy menu close >/dev/null 2>&1 || true

  if (( OPAQUE )) && [[ -f $GLASS_BACKUP ]]; then
    mv "$GLASS_BACKUP" "$TOGGLES/window-glassy.lua"
  fi

  hyprctl dispatch "hl.dsp.focus({ workspace = \"$PREVIOUS_WORKSPACE\" })" >/dev/null 2>&1 || true
  omarchy theme set "$PREVIOUS_THEME" >/dev/null 2>&1 || true
  exit $status
}
trap cleanup EXIT INT TERM

launch() { # class title command...
  local class=$1 title=$2
  shift 2
  setsid bash -c "cd '$REPO' && exec kitty --class '$class' --title '$title' $*" >/dev/null 2>&1 </dev/null &
  sleep 0.1
}

address_of() { # class
  local address
  for _ in $(seq 1 60); do
    address=$(hyprctl clients -j | jq -r --arg c "$1" '.[] | select(.class==$c) | .address' | head -1)
    if [[ -n $address ]]; then echo "$address"; return 0; fi
    sleep 0.25
  done
  return 1
}

geometry() { # address
  hyprctl clients -j | jq -r --arg a "$1" '.[] | select(.address==$a) | "\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"'
}

place() { # address x y w h
  local address=$1 x=$2 y=$3 w=$4 h=$5
  [[ -n $address ]] || { echo "no window to place at $x,$y" >&2; return 1; }
  for _ in 1 2 3 4; do
    hyprctl dispatch "hl.dsp.window.move({ workspace = \"$WS\", window = \"address:$address\" })" >/dev/null
    hyprctl dispatch "hl.dsp.window.float({ action = \"enable\", window = \"address:$address\" })" >/dev/null
    sleep 0.25
    hyprctl dispatch "hl.dsp.window.resize({ x = $w, y = $h, window = \"address:$address\" })" >/dev/null
    sleep 0.2
    hyprctl dispatch "hl.dsp.window.move({ x = $x, y = $y, window = \"address:$address\" })" >/dev/null
    sleep 0.2
    [[ $(geometry "$address") == "$x,$y ${w}x${h}" ]] && return 0
  done
  echo "window settled at $(geometry "$address"), wanted $x,$y ${w}x${h}" >&2
  return 1
}

focus_canvas() {
  hyprctl dispatch "hl.dsp.focus({ workspace = \"$WS\" })" >/dev/null
  sleep 0.9
}

shoot() { grim -o "$(hyprctl monitors -j | jq -r '.[] | select(.focused) | .name')" "$1"; }

mkdir -p "$OUT"

if (( OPAQUE )); then
  [[ -f $TOGGLES/window-glassy.lua ]] && mv "$TOGGLES/window-glassy.lua" "$GLASS_BACKUP"
fi

echo "theme: $TITLE (was $PREVIOUS_THEME)"
omarchy theme set "$TITLE" >/dev/null 2>&1
sleep 4

# 1. The specimen, alone on the wallpaper.
launch shot-preview "palette specimen" -e "$REPO/scripts/specimen.sh"
sleep 3
place "$(address_of shot-preview)" 150 170 720 400
focus_canvas
sleep 1
shoot "$REPO/preview.png"
echo "  preview.png"

# 2. Four windows tiled.
launch shot-btop btop -e btop
launch shot-lg lazygit -e lazygit
launch shot-nvim nvim -e nvim colors.toml
( cd "$REPO" && setsid flea "$REPO" >/dev/null 2>&1 </dev/null & )
sleep 5
place "$(address_of shot-btop)" 18 44 930 480
place "$(address_of shot-lg)" 960 44 942 480
place "$(address_of shot-nvim)" 960 536 942 526
place "$(address_of com.thisisgm.flea)" 18 536 930 526
focus_canvas
sleep 2
shoot "$OUT/tiled.png"
echo "  screenshots/tiled.png"

# 3. flea floating over the same layout.
place "$(address_of com.thisisgm.flea)" 400 200 1100 640
focus_canvas
sleep 1.2
shoot "$OUT/floating.png"
echo "  screenshots/floating.png"

# 4. The shell: menu over the desktop, then notifications.
for address in $(hyprctl clients -j | jq -r '.[] | select(.class|startswith("shot-")) | .address'); do
  hyprctl dispatch "hl.dsp.window.close({ window = \"address:$address\" })" >/dev/null 2>&1 || true
done
flea_address=$(hyprctl clients -j | jq -r '.[] | select(.class=="com.thisisgm.flea") | .address' | head -1)
  [[ -n $flea_address ]] && hyprctl dispatch "hl.dsp.window.close({ window = \"address:$flea_address\" })" >/dev/null 2>&1 || true
sleep 1
focus_canvas
omarchy menu summon >/dev/null 2>&1
sleep 1.8
shoot "$OUT/shell.png"
echo "  screenshots/shell.png"
omarchy menu close >/dev/null 2>&1

omarchy notification dismiss "Café des Deux Moulins" >/dev/null 2>&1 || true
omarchy notification dismiss "Amélie" >/dev/null 2>&1 || true
sleep 0.5
omarchy notification send -g "󰋜" "Amélie" "The awning is open: red for the one thing worth noticing." >/dev/null 2>&1
omarchy notification send -u critical -g "󰅶" "Café des Deux Moulins" "Kitchen closes at 22:00. Table 12, second sitting." >/dev/null 2>&1
sleep 2
shoot "$OUT/notifications.png"
echo "  screenshots/notifications.png"
omarchy notification dismiss "Café des Deux Moulins" >/dev/null 2>&1 || true
omarchy notification dismiss "Amélie" >/dev/null 2>&1 || true

# 5. The lock card needs no session.
python3 "$REPO/scripts/make-lock-preview.py"
echo "  preview-unlock.png"

echo
echo "Captured. Restoring $PREVIOUS_THEME on exit."
