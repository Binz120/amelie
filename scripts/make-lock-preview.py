#!/usr/bin/env python3
"""Render preview-unlock.png: the lock card over the theme's own wallpaper.

Omarchy's theme picker shows `preview.png` and `preview-unlock.png`. The first
is a desktop capture; this one is drawn, because locking a session to take a
screenshot needs the password to get back. The card is built from the `[lock]`
section of `shell.toml` and the wallpaper from `backgrounds/1.jpg`, so it shows
the real colours and the real image — it is a render, not a capture, and the
README says so.

    scripts/make-lock-preview.py [--out preview-unlock.png]
"""

from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parent.parent
COLORS = REPO / "colors.toml"
SHELL = REPO / "shell.toml"
WALLPAPER = REPO / "backgrounds" / "1.jpg"
FONT = REPO / "fonts" / "Lora-Regular.ttf"

WIDTH, HEIGHT = 1920, 1080


def parse_colors(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*\"?(#[0-9A-Fa-f]{6})\"?", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")[:6]
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def gradient(size, stops) -> Image.Image:
    """Diagonal two-stop gradient, top-left to bottom-right."""
    width, height = size
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            t = (x + y) / (width + height)
            pixels[x, y] = tuple(  # type: ignore[assignment]
                round(stops[0][i] * (1 - t) + stops[1][i] * t) for i in range(3)
            )
    return image


def rounded_mask(size, box, radius) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    return mask


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the lock-card preview.")
    parser.add_argument("--out", default=str(REPO / "preview-unlock.png"))
    args = parser.parse_args()

    colors = parse_colors(COLORS)
    shell = tomllib.loads(SHELL.read_text(encoding="utf-8"))
    lock = shell["lock"]

    # Background: the wallpaper, softened the way a lock screen hides the desktop.
    background = Image.open(WALLPAPER).convert("RGB")
    scale = max(WIDTH / background.width, HEIGHT / background.height)
    background = background.resize(
        (round(background.width * scale), round(background.height * scale)), Image.LANCZOS
    )
    left = (background.width - WIDTH) // 2
    top = (background.height - HEIGHT) // 2
    background = background.crop((left, top, left + WIDTH, top + HEIGHT))
    background = background.filter(ImageFilter.GaussianBlur(22))
    scrim = Image.new("RGB", (WIDTH, HEIGHT), rgb(colors["darker_background"]))
    background = Image.blend(background, scrim, 0.55)
    image = background.convert("RGBA")

    # Gradient ring: the same two stops the shell puts on the lock border.
    border_spec = lock.get("border", "hyprland.active-border")
    if border_spec in colors:
        spec = colors[border_spec]
    else:
        spec = colors.get("hyprland_active_border", "")
    stops = [rgb(match) for match in re.findall(r"(?:rgba?|#)\(?([0-9A-Fa-f]{6})", spec)]
    stops = stops or [rgb(colors["accent"]), rgb(colors["red"])]

    box = (620, 350, 1300, 700)
    radius = 14
    card = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    fill = (*rgb(lock["background"]), round(float(lock.get("background-alpha", 1)) * 255))
    ImageDraw.Draw(card).rounded_rectangle(box, radius=radius, fill=fill)
    image = Image.alpha_composite(image, card)

    ring = Image.composite(
        gradient((WIDTH, HEIGHT), (stops[0], stops[-1])).convert("RGBA"),
        Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0)),
        rounded_mask((WIDTH, HEIGHT), box, radius),
    )
    ring = Image.composite(
        ring,
        Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0)),
        Image.composite(
            rounded_mask((WIDTH, HEIGHT), box, radius),
            Image.new("L", (WIDTH, HEIGHT), 0),
            Image.eval(rounded_mask((WIDTH, HEIGHT), (box[0] + 2, box[1] + 2, box[2] - 2, box[3] - 2), radius - 2), lambda v: 255 - v),
        ),
    )
    image = Image.alpha_composite(image, ring)

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT), 26) if FONT.exists() else ImageFont.load_default()
    small = ImageFont.truetype(str(FONT), 20) if FONT.exists() else ImageFont.load_default()

    # Padlock: shackle arc over a rounded body, in brass.
    brass = (*rgb(colors["accent"]), 235)
    cx, cy = WIDTH // 2, 420
    draw.arc((cx - 20, cy - 26, cx + 20, cy + 14), 180, 360, fill=brass, width=5)
    draw.rounded_rectangle((cx - 27, cy - 2, cx + 27, cy + 38), radius=8, outline=brass, width=4)
    draw.ellipse((cx - 4, cy + 12, cx + 4, cy + 20), fill=brass)

    label = "Amélie"
    width = draw.textlength(label, font=font)
    draw.text(((WIDTH - width) / 2, cy + 58), label, font=font, fill=(*rgb(lock["text"]), 255))

    # The password field: shell.toml's lock placeholder on a darker inset.
    field = (760, 560, 1160, 616)
    draw.rounded_rectangle(field, radius=8, fill=(*rgb(colors["darker_background"]), 230),
                           outline=(*rgb(colors["muted"]), 120), width=1)
    placeholder = lock.get("placeholder", colors["muted"])
    draw.text((field[0] + 18, field[1] + 15), "Enter password", font=small,
              fill=(*rgb(placeholder), 235))
    caret_x = field[0] + 170
    draw.rectangle((caret_x, field[1] + 14, caret_x + 2, field[3] - 14),
                   fill=(*rgb(lock.get("selection", colors["accent"])), 200))

    hint = "Press Enter to unlock"
    hint_width = draw.textlength(hint, font=small)
    draw.text(((WIDTH - hint_width) / 2, field[3] + 26), hint, font=small,
              fill=(*rgb(colors["muted"]), 170))

    out = Path(args.out)
    image.convert("RGB").save(out, optimize=True)
    print(f"{out}  {WIDTH}x{HEIGHT}  {out.stat().st_size / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
