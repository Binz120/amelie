#!/usr/bin/env python3
"""Print the palette as a terminal specimen.

The same sheet appears in `preview.png`, and reading it from `colors.toml` means
a palette change shows up here before it reaches a screenshot.

    python3 scripts/specimen.py [--width 66]

Truecolor output; falls back to plain text when stdout is not a terminal.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COLORS = REPO / "colors.toml"


def parse(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*\"?(#[0-9A-Fa-f]{6})\"?", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


class Ink:
    def __init__(self, enabled: bool):
        self.enabled = enabled

    def fg(self, color: str, text: str) -> str:
        if not self.enabled:
            return text
        r, g, b = (int(color[i : i + 2], 16) for i in (1, 3, 5))
        return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

    def bg(self, color: str, text: str) -> str:
        if not self.enabled:
            return text
        r, g, b = (int(color[i : i + 2], 16) for i in (1, 3, 5))
        return f"\033[48;2;{r};{g};{b}m{text}\033[0m"


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the Amélie palette specimen.")
    parser.add_argument("--width", type=int, default=64)
    args = parser.parse_args()

    colors = parse(COLORS)
    ink = Ink(sys.stdout.isatty())
    width = args.width
    rule = ink.fg(colors["muted"], "─" * width)

    print()
    print(f" {ink.fg(colors['accent'], 'AMÉLIE')}   {ink.fg(colors['muted'], 'palette specimen')}")
    print(" " + rule)

    ansi = [
        ("black", "black"), ("red", "red"), ("green", "green"), ("yellow", "yellow"),
        ("blue", "blue"), ("magenta", "magenta"), ("cyan", "cyan"), ("white", "foreground"),
    ]
    bright = [
        ("br.black", "muted"), ("br.red", "bright_red"), ("br.green", "bright_green"),
        ("br.yellow", "bright_yellow"), ("br.blue", "bright_blue"),
        ("br.magenta", "bright_magenta"), ("br.cyan", "bright_cyan"),
        ("br.white", "bright_foreground"),
    ]
    for (left_label, left_key), (right_label, right_key) in zip(ansi, bright):
        left = ink.bg(colors[left_key], "      ")
        right = ink.bg(colors[right_key], "      ")
        left_text = f"{ink.fg(colors['foreground'], left_label):<18} {ink.fg(colors['muted'], colors[left_key])}"
        right_text = f"{ink.fg(colors['foreground'], right_label):<18} {ink.fg(colors['muted'], colors[right_key])}"
        print(f" {left} {left_text:<38} {right} {right_text}")

    print(" " + rule)
    for role, key, note in (
        ("field", "background", "the room"),
        ("text", "foreground", "body"),
        ("accent", "accent", "focus, links, functions"),
        ("error", "red", "the one thing to notice"),
    ):
        swatch = ink.bg(colors[key], "      ")
        print(f" {swatch} {ink.fg(colors[key], role):<10} {ink.fg(colors['muted'], colors[key])}  "
              f"{ink.fg(colors['dark_foreground'], note)}")

    print(" " + rule)
    print(f" {ink.fg(colors['blue'], 'function')} {ink.fg(colors['foreground'], 'greet(name)')}"
          f"{ink.fg(colors['dark_foreground'], ' -- ')}"
          f"{ink.fg(colors['green'], '\"bonjour \"')} {ink.fg(colors['foreground'], '.. name')}")
    print(f" {ink.fg(colors['bright_magenta'], 'local')} {ink.fg(colors['foreground'], 'thing')} = "
          f"{ink.fg(colors['orange'], '2')}{ink.fg(colors['dark_foreground'], ' -- ')}"
          f"{ink.fg(colors['muted'], 'every role coloured')}")
    print()
    print(f" {ink.fg(colors['muted'], 'Red is kept for the one thing worth noticing.')}")


if __name__ == "__main__":
    main()
