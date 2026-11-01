#!/usr/bin/env bash
# Render the intro clip that plays at login from the theme's still.
#
# Omarchy pairs `backgrounds/<name>.<ext>` with `backgrounds/intros/<name>.mp4`
# and crossfades into the still, so the clip has to end on the still exactly:
# a slow push-in that resolves to the untouched image. Five to seven seconds,
# silent -- the shell owns the fade.

set -euo pipefail

REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
STILL=${1:-$REPO/backgrounds/1.jpg}
OUT=${2:-$REPO/backgrounds/intros/1.mp4}
SECONDS_LENGTH=${3:-6}
FPS=30

command -v ffmpeg >/dev/null 2>&1 || { echo "ffmpeg is required" >&2; exit 1; }
[[ -f $STILL ]] || { echo "missing still: $STILL" >&2; exit 1; }

frames=$(( SECONDS_LENGTH * FPS ))
# 1.06 -> 1.00 over the clip; the last frame is the still as it sits on screen.
step=$(awk -v f="$frames" 'BEGIN { printf "%.8f", 0.06 / (f - 1) }')

mkdir -p "$(dirname -- "$OUT")"
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -i "$STILL" \
  -vf "scale=2560:1440,zoompan=z='if(eq(on,0),1.06,max(1.0,1.06-${step}*on))'\
:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${frames}:s=1920x1080:fps=${FPS},\
format=yuv420p" \
  -frames:v "$frames" -c:v libx264 -preset slow -crf 20 -movflags +faststart -an \
  "$OUT"

printf '%s  %ss  %s\n' "$OUT" "$SECONDS_LENGTH" "$(du -h "$OUT" | cut -f1)"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames \
  -of default=noprint_wrappers=1 "$OUT"
