# Omacalc in BWM

Omacalc is the original Qt Quick/C++ calculator from
[omacom/omacalc](https://github.com/omacom/omacalc), pinned to
`573d7106f5c6c0225864eb8634ae37ddcb657f63` (2026-11-09). Its source is MIT,
Copyright (c) 2026 David Heinemeier Hansson. The embedded iA Writer Mono S fonts
are unchanged and remain under OFL-1.1, copyright Information Architects Inc.,
based on IBM Plex (IBM Corp.). Copies of both licenses are in `licenses/` at
the repository root and installed beside the binary.

Install without sudo:

```bash
bash ~/.config/hypr/scripts/install-omacalc.sh
```

`--force` rebuilds the pinned version. The installer keeps its source Git cache
in `${XDG_DATA_HOME:-~/.local/share}/bwm/omacalc/source`, exports a clean build,
applies `theme-path.patch`, builds with Qt 6/qmake, and installs atomically to
`bwm/omacalc/bin/omacalc`. It installs the upstream desktop file/icon, its source
revision, the patch, and the MIT/OFL notices. `~/.local/bin/omacalc` points to
`hypr/scripts/bwm-omacalc`. The installer refuses to overwrite a different
user-owned launcher. It seeds colors from the current shell without changing
the wallpaper. `install.sh` runs this before its initial palette generation.

The only application change is `theme-path.patch`: an optional
`OMACALC_THEME_FILE` selects a native Omarchy `colors.toml`. Omacalc watches that
file and its containing directory (or nearest existing ancestor), reattaching
after atomic replacement. Without the override, its original Omarchy path and
behavior are retained. No UI, font, or calculation logic is changed.

The BWM launcher supplies `~/.local/state/bwm/omacalc/colors.toml`, respecting
an explicit `OMACALC_THEME_FILE` from the user. The shared Matugen template
`matugen/templates/omacalc-colors.toml` maps `surface`, `on_surface`, `primary`
and `primary_container` to Omarchy's `background`, `foreground`, `accent` and
`selection`. Omacalc infers dark/light from the background, as upstream does
when `mode` is absent. Existing palette engines render it:

- Retro static/dynamic: the existing native Omarchy-to-M3 mapping preserves
  those four original colors exactly, including installed community themes.
- default (end-4): Matugen regenerates it with the selected wallpaper/palette.
- Breeze: the existing Breeze-to-M3 mapping supplies its static colors.

An open calculator retints without a restart or clearing the current expression.
The common window rule keeps its native launch size and text scale. It is listed
in Apps in all skins and under Actions → Calculator in Retro. No shortcut is added.

Validation:

```bash
python3 -m unittest discover -s tests -p test_omacalc_themes.py
# With an exported upstream tree to which theme-path.patch has been applied:
mkdir -p /tmp/omacalc-theme-tests
cd /tmp/omacalc-theme-tests
qmake6 /path/to/hyprland-de/config/hypr/omacalc/theme-watch.pro OMACALC_SOURCE=/path/to/patched/source
make
QT_QPA_PLATFORM=offscreen ./theme-watch
# Upstream's own arithmetic, sizing, and theme-parser tests:
bash /path/to/patched/source/bin/test
```

The native watcher checks use temporary palette and settings files, preserving
the real home and desktop theme. They cover first-time creation, in-place writes,
repeated atomic replacement, dark/light changes and calculation preservation.
