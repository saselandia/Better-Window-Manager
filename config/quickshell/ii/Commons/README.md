# Omarchy shell libraries (vendored)

`Commons/` and `Ui/` are copied from Omarchy's shell (https://github.com/basecamp/omarchy,
branch `quattro`, `shell/Commons` and `shell/Ui`), MIT License, Copyright (c) David Heinemeier
Hansson (see `LICENSE.omarchy`). They let Omarchy bar plugins (which `import qs.Commons` /
`import qs.Ui`) run inside BWM's Retro bar (`modules/ii/bar/omarchy/`).

BWM changes, kept minimal so the files can be refreshed from upstream:
- `Commons/Color.qml`: `currentThemePath` is `~/.local/state/bwm/omarchy` (BWM's Omarchy
  palette: `colors.toml` + `shell.toml`, written by `hypr/scripts/bwm_omarchy.py`); both files
  are watched (`watchChanges` + `reload()`), because BWM rewrites them on every wallpaper change.
- `Commons/Style.qml`: `bwmScale` multiplies the font base size (and with it bar tokens and
  spacing); the Retro bar sets it to its height / 24.
- `Commons/I18n.qml`: without `OMARCHY_PATH`, strings come from `Commons/omarchy/default/i18n`
  (Omarchy's `default/i18n/{en,es}/shell.json` and `locales.json`).
- `Ui/ScreenMoveRemap.qml` is BWM's own and has its line in `Ui/qmldir`.
- IPC on the focused monitor: every bar has its own copy of a panel. `Ui/Panel.qml` exposes
  `ipcScreenName` and anchors its handlers in `Commons/IpcRegistry.qml` (`anchor`/`unanchor`),
  whose `leaderFor()` prefers the copy on `Hyprland.focusedMonitor`. `reconcile()` switches
  `enabled` itself, the old leader off first and the new one on a turn later, so Quickshell
  never sees two handlers on one target; `Commons/ShellIpc.qml` therefore starts `enabled: false`
  instead of binding it to `leads()`. `Hyprland.focusedMonitor` stays empty until focus first
  moves between monitors (and right after start it can name the wrong one), so the registry
  reads the focused output from `hyprctl -j activeworkspace` at start and follows
  `focusedmon`/`focusedmonv2` events (`focusedScreen`). No copy is switched on until that first
  answer (`focusKnown`, 2 s fallback): switching one on and handing over at load made Quickshell
  warn once per panel.

Last refreshed from `quattro` `d9cc361c` (2026-11-08): every other file in `Commons/` and `Ui/`
is identical to upstream. To refresh again, copy upstream's files and re-apply the list above.
