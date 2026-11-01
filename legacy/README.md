# Legacy app configs

These are colourings for Omarchy 2.x / 3.x applications. None of them is
installed by Omarchy 4, which draws notifications, the OSD and the launcher in
the Omarchy shell from `shell.toml`; they shipped in the theme while it was
being written on 3.8 and are kept here for anyone still running one of those
apps from another source.

They are **not** staged into the theme at set time unless you copy them back.

| File | App | How to use |
|---|---|---|
| `mako.ini` | mako notification daemon | `include=~/.local/state/omarchy/current/theme/legacy/mako.ini` in `~/.config/mako/config` |
| `swayosd.css` | swayosd | `swayosd-server --style ~/.local/state/omarchy/current/theme/legacy/swayosd.css` |
| `walker.css` | walker launcher | `[ui] theme = "…/current/theme/legacy/walker.css"` |

The colours match `colors.toml` at the time of writing. They are not covered by
`scripts/audit.py`, since they style apps the theme no longer targets.
