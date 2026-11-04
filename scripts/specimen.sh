#!/usr/bin/env bash
# Print the palette specimen and hold the window open for a capture.
# `capture-screenshots.sh` runs this inside kitty; the sheet is generated from
# colors.toml by scripts/specimen.py.
set -euo pipefail
cd "$(dirname -- "${BASH_SOURCE[0]}")/.." || exit 1
python3 scripts/specimen.py
exec sleep 600
