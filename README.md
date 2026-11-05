# Amélie

![Amélie: palette specimen over the theme wallpaper](preview.png?v=2)

An Omarchy theme after Jeunet's film. Delbonnel lit Montmartre in green and gold
and held red back for the few objects that carry the story; the palette works
the same way here. Onyx green field, wheat light, brass chrome, and the café
awning's red kept for the one thing that should be noticed: errors, attention
marks and the active window border.

The film's pleasure is in small tactile things, and the theme is built out of
them: brass, enamel, lamplight, and a green that is always a room.

## Screenshots

The preview above is the palette specimen in a 720x400 terminal over the
theme's own wallpaper, with the bar above it.

![the lock card over the blurred wallpaper](preview-unlock.png)

`preview-unlock.png` is rendered from the `[lock]` section of `shell.toml` over
the actual wallpaper, not captured: locking a session to photograph it needs
the password to get back.

Captures of running apps are not committed — they show whatever is installed on
the machine that took them.

## Install

```bash
omarchy theme install https://github.com/Binz120/amelie
omarchy theme set amelie
```

The repository ships only what a theme install applies: the palette, the shell
surfaces, the colour files and the artwork are all of it. Omarchy renders the
terminals, the editors and the other apps from `colors.toml`.

Backgrounds: `Super + Ctrl + Space` or `omarchy theme bg next`.

## Palette

Twelve anchors arrived as a list and are used directly; every other role walks
one of those anchors in OKLCH — same hue, different lightness and chroma —
because a dark theme cannot print `#A4161A` as text (1.56:1) and stay readable.

| Role | Colour | Anchor | Contrast on the field |
|---|---|---|---|
| Field (background) | `#2B3A2A` | Onyx | n/a |
| Panels (dark background) | `#212E20` | Onyx L 0.285 | n/a |
| Deepest chrome | `#182417` | Onyx L 0.245 | n/a |
| Body text (foreground) | `#F5E1B8` | Wheat Light | 9.39 |
| Cursor (bright foreground) | `#FFF9EA` | Wheat Light L 0.985 | 11.48 |
| Dim text (dark foreground) | `#76914C` | Green Olive L 0.62 | 3.40 (chrome) |
| Comments (muted) | `#839D5C` | Green Olive L 0.66 | 3.99 (chrome) |
| Accent: focus, links, functions | `#E8B04A` | Honey | 6.17 |
| Selection | `#2E5B34` | Military Green | 6.14 with wheat on it |
| Keywords | `#FEF2D9` | Wheat L 0.965 | 10.86 |
| Types | `#E8C87E` | Caramel L 0.845 | 7.46 |
| Numbers | `#E9C46A` | Saffron | 7.22 |
| Strings | `#B5D28E` | Green Olive L 0.825 | 7.22 |
| Parameters, properties | `#9ECBA6` | Military Green L 0.80 | 6.63 |
| Errors, deletions | `#F67D72` | Red Ruby L 0.725 | 4.65 |
| ANSI magenta | `#E4887A` | Rust L 0.72 | 4.65 |
| ANSI brown | `#885E41` | Black of Jay L 0.52 | 2.14 (chrome) |

Reds never carry body text below the error role. `#D64933` (vermillon) and the
values around it sit at 2.79:1 on the field, so they are used as surfaces and as
the border gradient stop, not as type — the bar's attention role uses the lifted
ruby at 5.48:1 on the bar instead.

Three roles are deliberately low-contrast chrome, and say so: `muted` (3.99) for
comments and placeholders, `dark_foreground` (3.40) for line numbers and ANSI 8,
and `brown` (2.14) for the eighth ANSI hue. Everything else clears 4.5 on both
the field and the panel; every hex literal in the hand-written configs traces
back to a `colors.toml` role or a documented extension.

## The border

`colors.toml` carries the awning as a two-stop gradient on the active window and
on grouped windows:

```toml
hyprland_active_border = "rgba(d64933ee) rgba(e8b04aee) 45deg"
hyprland_inactive_border = "rgba(2e5b34aa)"
```

Omarchy renders that gradient into the compositor's config at staging, straight
from `colors.toml`; the border cannot drift from the palette.

## What the theme ships

| File | What it does |
|---|---|
| `colors.toml` | The palette. Omarchy generates terminals, Neovim, Helix, VS Code, fcitx5, the shell, the AI CLIs and GTK from it at staging. |
| `shell.toml` | The shell surfaces: bar two steps darker than the windows, awning gradient on popups, menus, notifications, launcher, polkit and the lock card. |
| `gtk.css` | GTK3/4 and libadwaita sheet: Lora on titles, menus and headerbars, sans body. Imported by `~/.config/gtk-4.0/gtk.css`. |
| `btop.theme` | Graphs warm from green to brass as they rise; heat burns honey-white. |
| `icons.theme` | `Yaru-sage-dark`. |
| `fastfetch.jsonc` | fastfetch layout in the theme palette: logo, hardware / software / age sections drawn in olive rules, keys in sage, honey and rust. |
| `starship.toml`, `lazygit.yml`, `fzf.sh` | Prompt, git TUI and fuzzy finder colours. |
| `zed.json`, `warp.yaml`, `vencord.theme.css` | Editor, terminal and Discord themes; each app imports its file by hand (see below). |
| `base24.yaml` | The palette in Base24 form, for any tool that consumes that spec. |
| `chromium.theme` | `43,58,42`. |
| `legacy/` | Colourings for the Omarchy 2.x / 3.x apps that were replaced by the shell. Not staged by default; see `legacy/README.md`. |
| `backgrounds/` | One still, `1.jpg` (2560x1440), and its intro clip `intros/1.mp4`. |
| `fonts/` | Lora Regular and Italic (SIL OFL 1.1). `gtk.css` asks for Lora on titles; put the two files in `~/.local/share/fonts`. |
| `preview.png`, `preview-unlock.png` | Theme-picker previews: the desktop, and the lock card rendered from `shell.toml`. |

Omarchy generates the files the theme does not repeat: terminals (four), Neovim,
Helix, VS Code, fcitx5, Obsidian, keyboard backlight, and the AI CLI configs.

## Apps outside Omarchy's own theming

The colour files cover the apps that read a user-level config of their own; each
one imports its file by hand:

```bash
# lazygit
mkdir -p ~/.config/lazygit && ln -sfn ~/.local/state/omarchy/current/theme/lazygit.yml ~/.config/lazygit/config.yml

# starship
ln -sfn ~/.local/state/omarchy/current/theme/starship.toml ~/.config/starship.toml

# fastfetch
mkdir -p ~/.config/fastfetch && ln -sfn ~/.local/state/omarchy/current/theme/fastfetch.jsonc ~/.config/fastfetch/config.jsonc

# fzf: source the active theme's colours from your shell rc
source ~/.local/state/omarchy/current/theme/fzf.sh

# Vencord / Vesktop: copy into the themes folder and enable it in settings
cp ~/.local/state/omarchy/current/theme/vencord.theme.css ~/.config/Vencord/themes/

# Zed: copy into ~/.config/zed/themes/ and pick "Amélie"
cp ~/.local/state/omarchy/current/theme/zed.json ~/.config/zed/themes/

# Warp: copy into ~/.warp/themes/
mkdir -p ~/.warp/themes && cp ~/.local/state/omarchy/current/theme/warp.yaml ~/.warp/themes/
```

Steam is not covered: neither Omarchy nor Steam exposes a palette hook a theme
can write, so a `steam.css` here would be decoration. Waterfox and other
Firefox-derived browsers are not covered either: they read `userChrome.css`
rather than colour values.

## The wallpaper

`backgrounds/1.jpg` is drawn from the palette: the onyx room, a café window of
brass bokeh behind its mullions, the awning's scalloped valance along the bottom
and the café name tracked in the corner. It carries no third-party image.

`backgrounds/intros/1.mp4` is the still with a slow push-in that resolves to it
exactly, six seconds and silent. The shell crossfades into the still, so no fade
of its own is needed.

## Credits and licence

Theme and artwork: MIT (see `LICENSE`). Lora is by the Lora Project Authors
under the SIL Open Font License 1.1 (`fonts/OFL.txt`). Icons are `Yaru-sage-dark`
from the Yaru project, and are not redistributed here.
