#!/usr/bin/env python3
"""Draw Amélie's wallpaper from the theme palette.

A night interior after Delbonnel: the onyx-green room, a window of brass lamp
bokeh, the café awning's red held along the bottom, and the café name tracked
small in the corner. Every colour comes from `colors.toml`, and the seed is
fixed, so the same palette always draws the same image.

    scripts/make-background.py [--size 2560x1440] [--out backgrounds/1.jpg]

Pillow only. Writes JPEG at quality 92.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parent.parent
COLORS = REPO / "colors.toml"

FALLBACK = {
    "background": "#2B3A2A",
    "dark_background": "#212E20",
    "darker_background": "#182417",
    "foreground": "#F5E1B8",
    "accent": "#E8B04A",
    "yellow": "#E8C87E",
    "orange": "#E9C46A",
    "red": "#F67D72",
    "brown": "#885E41",
}

# The two anchors the palette holds back from the rest of the theme.
VERMILLON = (214, 73, 51)  # #D64933, the awning
VERMILLON_DEEP = (104, 33, 26)
BRASS = (201, 161, 59)  # #C9A13B, caramel

FONT_CANDIDATES = (
    "/usr/share/fonts/TTF/Lora-Regular.ttf",
    str(Path.home() / ".local/share/fonts/Lora.ttf"),
    "/usr/share/fonts/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSerif.ttf",
)
ITALIC_CANDIDATES = (
    "/usr/share/fonts/TTF/Lora-Italic.ttf",
    str(Path.home() / ".local/share/fonts/Lora-Italic.ttf"),
    "/usr/share/fonts/liberation/LiberationSerif-Italic.ttf",
    "/usr/share/fonts/TTF/DejaVuSerif-Italic.ttf",
)


def load_colors(path: Path) -> dict[str, str]:
    colors = dict(FALLBACK)
    if not path.exists():
        return colors
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip("\"'")
        if value.startswith("#") and len(value) in (7, 9):
            colors[key.strip()] = value
    return colors


def rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")[:6]
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def mix(a, b, amount: float) -> tuple[int, int, int]:
    return tuple(round(a[i] * (1 - amount) + b[i] * amount) for i in range(3))  # type: ignore[return-value]


def vertical_gradient(size, stops):
    width, height = size
    column = Image.new("RGB", (1, height))
    pixels = column.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                pixels[0, y] = mix(c0, c1, (t - p0) / max(p1 - p0, 1e-6))
                break
        else:
            pixels[0, y] = stops[-1][1]
    return column.resize((width, height), Image.BILINEAR)


def soft_disc(layer, center, radius, color, alpha):
    """A bokeh disc: bright rim, soft body."""
    x, y = (int(round(v)) for v in center)
    radius = max(2, int(round(radius)))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                 fill=(*color, int(alpha)))
    inner = int(radius * 0.74)
    draw.ellipse((x - inner, y - inner, x + inner, y + inner),
                 fill=(*color, max(int(alpha) - 8, 0)))
    draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                 outline=(*color, min(255, int(alpha) + 55)),
                 width=max(1, radius // 12))


def window_mask(size, colors) -> Image.Image:
    """The tall café window the lamps are seen through, with its mullions."""
    width, height = size
    x0, x1 = int(width * 0.52), int(width * 0.985)
    y0, y1 = int(height * 0.01), int(height * 0.44)

    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((x0, y0, x1, y1), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(width * 0.018))

    frame = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame, "RGBA")
    # Mullions sit in front of the light, so they cut the bokeh down.
    for x in (0.60, 0.72, 0.84, 0.96):
        draw.rectangle((int(width * x), y0, int(width * x) + 9, y1),
                       fill=(*rgb(colors["darker_background"]), 235))
    for y in (0.20, 0.38):
        draw.rectangle((x0, int(height * y), x1, int(height * y) + 9),
                       fill=(*rgb(colors["darker_background"]), 235))
    # The frame itself, so the panes end at an edge instead of the screen.
    draw.rectangle((x0, y0, x1, y1), outline=(*rgb(colors["darker_background"]), 245), width=14)
    return mask, frame


def draw_bokeh(size, colors, rng):
    width, height = size
    mask, frame = window_mask(size, colors)

    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    warm = [rgb(colors["accent"]), rgb(colors["yellow"]), rgb(colors["orange"]),
            rgb(colors["foreground"]), rgb(colors["brown"])]

    for cx, cy, spread_x, spread_y, count in (
        (0.72, 0.16, 0.13, 0.07, 60),
        (0.90, 0.28, 0.07, 0.07, 30),
        (0.60, 0.30, 0.06, 0.05, 18),
    ):
        for _ in range(count):
            gx = rng.gauss(cx, spread_x)
            gy = rng.gauss(cy, spread_y)
            if not (0 <= gx <= 1 and 0 <= gy <= 1):
                continue
            radius = rng.choice((4, 6, 9, 12, 16, 21, 27)) * rng.uniform(0.8, 1.2)
            soft_disc(layer, (gx * width, gy * height), radius,
                      rng.choice(warm), rng.randint(16, 52))

    layer = layer.filter(ImageFilter.GaussianBlur(6))
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))

    cores = Image.new("RGBA", size, (0, 0, 0, 0))
    for _ in range(26):
        gx = rng.gauss(0.74, 0.11)
        gy = rng.gauss(0.18, 0.08)
        if not (0 <= gx <= 1 and 0 <= gy <= 1):
            continue
        soft_disc(cores, (gx * width, gy * height), rng.uniform(1.3, 3.2),
                  rgb(colors["yellow"]), 170)
    cores = cores.filter(ImageFilter.GaussianBlur(0.9))
    cores.putalpha(ImageChops.multiply(cores.getchannel("A"), mask))

    return Image.alpha_composite(Image.alpha_composite(layer, cores), frame)


def draw_room(size, colors) -> Image.Image:
    """Lamp pool and the two interior walls, before the bokeh."""
    width, height = size
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow, "RGBA")
    cx, cy = width * 0.70, height * 0.24
    for step in range(9, 0, -1):
        r = width * 0.05 * step
        draw.ellipse((cx - r, cy - r * 0.8, cx + r, cy + r * 0.8),
                     fill=(*rgb(colors["accent"]), 6 + 2 * (9 - step)))
    room = glow.filter(ImageFilter.GaussianBlur(width * 0.03))

    walls = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(walls, "RGBA")
    draw.polygon([(0, 0), (width * 0.10, 0), (width * 0.02, height), (0, height)],
                 fill=(*rgb(colors["darker_background"]), 140))
    draw.polygon([(width, 0), (width * 0.90, 0), (width * 0.98, height), (width, height)],
                 fill=(*rgb(colors["darker_background"]), 140))
    walls = walls.filter(ImageFilter.GaussianBlur(width * 0.012))
    return Image.alpha_composite(room, walls)


def draw_awning(size, colors) -> Image.Image:
    """The café awning: a scalloped valance hanging into the frame."""
    width, height = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")

    scallops = 18
    stripe = width / scallops
    radius = stripe / 2
    band_top = int(height * 0.884)
    valance_top = band_top - int(radius * 0.78)
    rod_y = valance_top - 9

    # The room's shadow under the rod, so the fabric sits in front of the field.
    for i in range(48):
        t = i / 47
        draw.rectangle((0, rod_y - 60 + int(60 * t), width, rod_y),
                       fill=(*rgb(colors["darker_background"]), int(7 * (1 - t))))

    # Fabric across the full canvas; a mask cuts it to the scalloped edge.
    fabric = Image.new("RGB", (width, height))
    pixels = fabric.load()
    shade = []
    for x in range(width):
        u = (x % stripe) / stripe
        shade.append(0.74 + 0.26 * math.sin(math.pi * u) ** 0.6)
    for y in range(height):
        if y < valance_top:
            continue
        t = (y - valance_top) / max(height - valance_top - 1, 1)
        base = mix(VERMILLON, VERMILLON_DEEP, 0.62 + 0.30 * t)
        if y < band_top:
            base = mix(base, rgb(colors["accent"]), 0.10)
        for x in range(width):
            pixels[x, y] = mix((0, 0, 0), base, shade[x])

    fabric_draw = ImageDraw.Draw(fabric, "RGBA")
    for index in range(scallops + 1):
        x = min(width - 1, int(index * stripe))
        fabric_draw.line((x, valance_top, x, height), fill=(6, 4, 4, 85), width=3)
    fabric = fabric.filter(ImageFilter.GaussianBlur(0.5))

    mask = Image.new("L", size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rectangle((0, band_top, width, height), fill=255)
    for index in range(scallops):
        cx = (index + 0.5) * stripe
        mask_draw.ellipse((cx - radius, band_top - radius * 0.78,
                           cx + radius, band_top + radius * 0.78), fill=255)
    fabric.putalpha(ImageChops.multiply(fabric.convert("RGBA").getchannel("A"), mask))
    layer = Image.alpha_composite(layer, fabric.convert("RGBA"))

    draw = ImageDraw.Draw(layer, "RGBA")
    for index in range(scallops):
        cx = (index + 0.5) * stripe
        draw.arc((cx - radius, band_top - radius * 0.78,
                  cx + radius, band_top + radius * 0.78),
                 180, 360, fill=(*BRASS, 130), width=2)

    draw.line((0, rod_y, width, rod_y), fill=(*BRASS, 210), width=3)
    draw.line((0, rod_y + 4, width, rod_y + 4), fill=(0, 0, 0, 95), width=2)
    return layer


def draw_type(size, colors) -> Image.Image:
    width, height = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")

    font = None
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            font = ImageFont.truetype(candidate, 27)
            break
    if font is None:
        font = ImageFont.load_default()

    text = "CAFÉ DES DEUX MOULINS"
    tracking = 10
    widths = [draw.textlength(char, font=font) for char in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = width - total - int(width * 0.055)
    y = int(height * 0.735)

    draw.line((x, y - 20, x + total, y - 20), fill=(*BRASS, 70), width=1)
    cursor = x
    for char, char_width in zip(text, widths):
        draw.text((cursor, y), char, font=font, fill=(*rgb(colors["foreground"]), 150))
        cursor += char_width + tracking

    italic = None
    for candidate in ITALIC_CANDIDATES:
        if Path(candidate).exists():
            italic = ImageFont.truetype(candidate, 33)
            break
    if italic is not None:
        draw.text((x + 2, y + 42), "Montmartre, 1997", font=italic,
                  fill=(*rgb(colors["brown"]), 135))

    return layer


def draw_vignette(size) -> Image.Image:
    width, height = size
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse(
        (-int(width * 0.06), -int(height * 0.06), width + int(width * 0.06), height + int(height * 0.06)),
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(min(width, height) * 0.09))
    dark = Image.new("RGBA", size, (10, 16, 10, 255))
    dark.putalpha(ImageChops.invert(mask).point(lambda v: int(v * 0.5)))
    return dark


def draw_grain(size, rng) -> Image.Image:
    noise = Image.effect_noise(size, 16).convert("L")
    layer = Image.new("RGBA", size, (255, 255, 255, 0))
    layer.putalpha(noise.point(lambda v: int(abs(v - 128) * 0.18)))
    return layer


def render(size, colors) -> Image.Image:
    rng = random.Random(1997)

    image = vertical_gradient(
        size,
        [
            (0.00, mix(rgb(colors["darker_background"]), (0, 0, 0), 0.12)),
            (0.30, mix(rgb(colors["dark_background"]), rgb(colors["background"]), 0.30)),
            (0.62, rgb(colors["background"])),
            (0.85, mix(rgb(colors["background"]), rgb(colors["darker_background"]), 0.55)),
            (1.00, rgb(colors["darker_background"])),
        ],
    ).convert("RGBA")

    image = Image.alpha_composite(image, draw_room(size, colors))
    image = ImageChops.screen(
        image.convert("RGB"), draw_bokeh(size, colors, rng).convert("RGB")
    ).convert("RGBA")
    image = Image.alpha_composite(image, draw_awning(size, colors))
    image = Image.alpha_composite(image, draw_type(size, colors))
    image = Image.alpha_composite(image, draw_vignette(size))
    image = Image.alpha_composite(image, draw_grain(size, rng))

    return image.convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw the Amélie wallpaper.")
    parser.add_argument("--size", default="2560x1440")
    parser.add_argument("--out", default=str(REPO / "backgrounds" / "1.jpg"))
    parser.add_argument("--preview", default="")
    args = parser.parse_args()

    width, height = (int(part) for part in args.size.lower().split("x"))
    image = render((width, height), load_colors(COLORS))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, quality=92, subsampling=0, optimize=True)
    print(f"{out}  {image.width}x{image.height}  {out.stat().st_size / 1024:.0f} KiB")

    if args.preview:
        preview = image.copy()
        preview.thumbnail((1280, 1280), Image.LANCZOS)
        Path(args.preview).parent.mkdir(parents=True, exist_ok=True)
        preview.save(args.preview, quality=88)
        print(f"{args.preview}  {preview.width}x{preview.height}")


if __name__ == "__main__":
    main()
