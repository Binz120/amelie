#!/usr/bin/env python3
"""Check Amélie's palette and the colours the hand-written configs spell out.

Two questions, both about drift:

1. Is every role the theme uses as text readable on both surfaces the theme
   paints them on? The thresholds are the ones the README publishes.
2. Does every hex literal in the hand-written configs come from `colors.toml`?
   A colour that does not is either a documented extension (listed below) or a
   value someone typed once and never updated.

    scripts/audit.py [--quiet]

Exits non-zero on any failure, so CI and `scripts/verify.sh` can use it.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COLORS = REPO / "colors.toml"

# Text roles must clear this on background and dark_background.
TEXT_MIN = 4.5
# Roles that are chrome by design. Each floor is what the README claims.
CHROME_FLOORS = {
    "muted": 3.5,          # comments, placeholders, dim labels
    "dark_foreground": 3.0,  # ANSI 8, line numbers
    "brown": 2.0,          # ANSI 8th hue: 2.14 on the field, never body text
}

# Colours the hand-written configs spell out that are not `colors.toml` roles.
# Surfaces, mixes and app-specific states live here, with the reason.
EXTENSIONS = {
    "#1C2A1E": "terminal ANSI black, used as a text-view surface",
    "#6E8B3D": "olive anchor: the graph low stop in btop",
    "#C9A13B": "caramel anchor: btop boxes and the shell's idle control border",
    "#F2D49B": "wheat anchor: tooltip text and btop graph text (11.9:1 on the tooltip)",
    "#3D2B1F": "black of jay, the warm neutral the palette left as an anchor only",
    "#111A10": "Base24 base11, the darkest surface (darker_background deepened)",
    "#434E3B": "Vencord raised surface (background mixed toward foreground)",
    "#4B5541": "Vencord raised surface, one step higher",
    "#535B46": "Vencord raised surface, highest",
    "#D8D0A1": "Vencord muted text (wheat mixed toward the field)",
    "#ECBE6B": "Vencord primary button hover (accent lifted)",
    "#BE903D": "Vencord primary button active (accent deepened)",
    "#000000": "button text on a filled accent control",
}

CONFIG_FILES = (
    "shell.toml",
    "gtk.css",
    "btop.theme",
    "fzf.sh",
    "starship.toml",
    "lazygit.yml",
    "zed.json",
    "warp.yaml",
    "vencord.theme.css",
    "fastfetch.jsonc",
    "base24.yaml",
)


def parse_colors(path: Path) -> dict[str, str]:
    """key = "#RRGGBB"  # comments after the value are allowed."""
    colors: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*\"?(#[0-9A-Fa-f]{6})\"?", line)
        if match:
            colors[match.group(1)] = match.group(2).upper()
    return colors


def luminance(hex_color: str) -> float:
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the Amélie palette.")
    parser.add_argument("--quiet", action="store_true", help="only print failures")
    args = parser.parse_args()

    colors = parse_colors(COLORS)
    if not colors:
        print("colors.toml has no colours", file=sys.stderr)
        return 2

    failures: list[str] = []
    surfaces = {"background": colors["background"], "dark_background": colors["dark_background"]}

    text_roles = [
        key for key in colors
        if key not in CHROME_FLOORS
        and key not in ("background", "dark_background", "darker_background", "lighter_background")
        and key not in ("selection", "selection_background", "selection_foreground")
        and key not in ("hyprland_active_border", "hyprland_inactive_border", "mode")
    ]

    rows = []
    for role in sorted(text_roles):
        worst = min(contrast(colors[role], bg) for bg in surfaces.values())
        label = next(name for name, value in surfaces.items() if value == min(surfaces.values(), key=lambda s: contrast(colors[role], s)))
        rows.append((role, colors[role], worst, label, TEXT_MIN))
        if worst < TEXT_MIN:
            failures.append(f"{role} {colors[role]} is {worst:.2f}:1 on {label} (needs {TEXT_MIN})")

    for role, floor in CHROME_FLOORS.items():
        if role not in colors:
            failures.append(f"{role} is missing from colors.toml")
            continue
        worst = min(contrast(colors[role], bg) for bg in surfaces.values())
        rows.append((role, colors[role], worst, "chrome", floor))
        if worst < floor:
            failures.append(f"{role} {colors[role]} is {worst:.2f}:1 (chrome floor {floor})")

    if not args.quiet:
        print("Role                      Colour    Worst contrast   Floor")
        for role, value, worst, where, floor in rows:
            flag = " " if worst >= floor else "!"
            print(f"{flag} {role:<22} {value:<9} {worst:5.2f}:1 {where:<15} {floor}")

    # Every hex in the hand-written configs has to come from the palette.
    palette = set(colors.values())
    seen: dict[str, list[str]] = {}
    for name in CONFIG_FILES:
        path = REPO / name
        if not path.exists():
            continue
        for match in re.findall(r"#[0-9A-Fa-f]{6}\b", path.read_text(encoding="utf-8")):
            seen.setdefault(match.upper(), []).append(name)

    stray = {value: files for value, files in seen.items() if value not in palette and value not in EXTENSIONS}
    for value, files in sorted(stray.items()):
        failures.append(f"{value} in {', '.join(sorted(set(files)))} is not in colors.toml")

    # chromium.theme is an R,G,B triple of the field.
    chromium = REPO / "chromium.theme"
    if chromium.exists():
        expected = ",".join(str(int(colors["background"][i : i + 2], 16)) for i in (1, 3, 5))
        actual = chromium.read_text(encoding="utf-8").strip().strip("\"'")
        if actual != expected:
            failures.append(f"chromium.theme is {actual}, background is {expected}")

    if failures:
        print()
        for failure in failures:
            print(f"FAIL  {failure}")
        return 1

    if not args.quiet:
        print()
        print(f"{len(rows)} roles checked, {len(seen)} hex literals traced to colors.toml or documented extensions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
