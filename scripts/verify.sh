#!/usr/bin/env bash
# Everything that can be checked without looking at the screen.
#
#   scripts/verify.sh          palette audit + file checks + a real staging run
#   scripts/verify.sh --fast   skip the staging run (what CI does)
#
# The staging run uses a throwaway HOME and re-applies the theme twice: once as
# a clone (with a .git directory) and once as a hand-written copy. Omarchy drops
# Lua, the terminal configs and vscode.json from a clone and regenerates them;
# the two staged trees have to come out byte-identical, which is the check that
# keeps the theme from looking different depending on how it was installed.

set -uo pipefail

REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
FAST=0
[[ ${1:-} == "--fast" ]] && FAST=1

failures=0
step() { printf '\n== %s\n' "$*"; }
ok() { printf '  ok    %s\n' "$*"; }
bad() { printf '  FAIL  %s\n' "$*"; failures=$((failures + 1)); }

cd "$REPO" || exit 1

step "palette"
if python3 scripts/audit.py; then ok "contrast and colour provenance"; else bad "palette audit"; fi

step "files parse"
python3 - "$REPO" <<'PY'
import json, sys, tomllib
from pathlib import Path

repo = Path(sys.argv[1])
failed = []

for path in sorted(repo.glob("*.toml")) + sorted(repo.glob("legacy/*.toml")):
    try:
        tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        failed.append(f"{path.name}: {error}")

for path in sorted(repo.glob("*.json")) + sorted(repo.glob("*.jsonc")):
    text = path.read_text(encoding="utf-8")
    # jsonc: strip // and /* */ comments outside strings, and trailing commas.
    out, i, in_string, escape = [], 0, False, False
    while i < len(text):
        char = text[i]
        if in_string:
            out.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            i += 1
        elif char == '"':
            in_string = True
            out.append(char)
            i += 1
        elif text.startswith("//", i):
            while i < len(text) and text[i] != "\n":
                i += 1
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = len(text) if end == -1 else end + 2
        else:
            out.append(char)
            i += 1
    cleaned = "".join(out)
    cleaned = cleaned.replace(",\n    }", "\n    }").replace(",\n  }", "\n  }")
    try:
        json.loads(cleaned)
    except Exception as error:
        failed.append(f"{path.name}: {error}")

try:
    import yaml
except ImportError:
    yaml = None
if yaml is not None:
    for path in sorted(repo.glob("*.yaml")) + sorted(repo.glob("*.yml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as error:
            failed.append(f"{path.name}: {error}")

for name in failed:
    print(f"  FAIL  {name}")
sys.exit(1 if failed else 0)
PY
if [[ $? -eq 0 ]]; then ok "TOML, JSON(C) and YAML in the tree"; else bad "unparseable config"; fi

step "assets"
background=backgrounds/1.jpg
if [[ -f $background ]]; then
  size=$(identify -format '%wx%h' "$background" 2>/dev/null || echo "unknown")
  [[ $size == "2560x1440" ]] && ok "$background $size" || bad "$background is $size, expected 2560x1440"
else
  bad "$background is missing (run scripts/make-background.py)"
fi
for asset in preview.png preview-unlock.png screenshots/tiled.png screenshots/floating.png screenshots/shell.png; do
  [[ -f $asset ]] && ok "$asset" || bad "$asset is missing"
done
if [[ -f backgrounds/intros/1.mp4 ]]; then
  ok "backgrounds/intros/1.mp4"
else
  bad "backgrounds/intros/1.mp4 is missing (run scripts/make-intro.sh)"
fi

step "no unresolved templates"
unresolved=$(grep -rIl '{{' --include='*.toml' --include='*.css' --include='*.conf' \
  --include='*.ini' --include='*.json' --include='*.jsonc' --include='*.yml' \
  --include='*.yaml' --include='*.sh' --include='*.lua' --include='*.theme' \
  --exclude-dir=scripts --exclude-dir=.git . 2>/dev/null || true)
if [[ -z $unresolved ]]; then ok "no {{ placeholders left in text files"; else bad "unresolved: $unresolved"; fi

if (( FAST )); then
  printf '\n%d failure(s)\n' "$failures"
  exit $(( failures > 0 ))
fi

step "staging"
if ! command -v omarchy-theme-set >/dev/null 2>&1; then
  printf '  skip  omarchy-theme-set not on PATH\n'
else
  work=$(mktemp -d)
  trap 'rm -rf "$work"' EXIT

  stage() { # $1 = repo name, $2 = keep .git
    local home="$work/$1"
    mkdir -p "$home/.config/omarchy/themes/amelie"
    # Mirror install.sh: the theme payload only, no dev tooling.
    (cd "$REPO" && tar -cf - --exclude='.git' --exclude='.github' \
      --exclude='scripts' --exclude='hooks' --exclude='extras' .) |
      (cd "$home/.config/omarchy/themes/amelie" && tar -xf -)
    if [[ ${2:-} == "git" ]]; then
      mkdir -p "$home/.config/omarchy/themes/amelie/.git"
    fi
    HOME="$home" OMARCHY_PATH="${OMARCHY_PATH:-/usr/share/omarchy}" \
      OMARCHY_THEME_HEADLESS=1 OMARCHY_THEME_SKIP_BACKGROUND=1 \
      omarchy-theme-set amelie >/dev/null 2>"$work/$1.err" || return 1
    echo "$home/.local/state/omarchy/current/theme"
  }

  clone_tree=$(stage clone git) || bad "theme set as a clone"
  local_tree=$(stage local) || bad "theme set as a hand-written copy"

  if [[ -n ${clone_tree:-} && -n ${local_tree:-} ]]; then
    if diff -rq "$clone_tree" "$local_tree" >"$work/diff"; then
      ok "clone and local staging are identical ($(find "$clone_tree" -type f | wc -l) files)"
    else
      bad "clone and local staging differ:"
      sed 's/^/          /' "$work/diff"
    fi

    for required in colors.toml shell.toml hyprland.lua gtk.css \
      alacritty.toml foot.ini kitty.conf ghostty.conf neovim.lua vscode-theme.json \
      btop.theme fastfetch.jsonc starship.toml lazygit.yml fzf.sh; do
      [[ -f $clone_tree/$required ]] || bad "$required missing from the staged theme"
    done

    if grep -q 'colors = {' "$clone_tree/hyprland.lua"; then
      ok "hyprland.lua carries the two-stop gradient"
    else
      bad "hyprland.lua lost its gradient"
    fi

    if grep -rIl '{{' --include='*.toml' --include='*.css' --include='*.conf' \
      --include='*.ini' --include='*.json' --include='*.jsonc' --include='*.yml' \
      --include='*.yaml' --include='*.lua' --include='*.theme' \
      "$clone_tree" 2>/dev/null | grep -q .; then
      bad "unresolved placeholders in the staged theme"
    else
      ok "no unresolved placeholders after staging"
    fi

    if [[ -s $work/clone.err ]]; then
      ok "clone install named what it dropped:"
      sed 's/^/          /' "$work/clone.err"
    fi
  fi
fi

printf '\n%d failure(s)\n' "$failures"
exit $(( failures > 0 ))
