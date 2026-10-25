# Omarchy shell libraries (vendored)

`Commons/` and `Ui/` are copied from Omarchy's shell (https://github.com/basecamp/omarchy,
branch `quattro`, `shell/Commons` and `shell/Ui`), MIT License, Copyright (c) David Heinemeier
Hansson (see `LICENSE.omarchy`). They let Omarchy bar plugins (which `import qs.Commons` /
`import qs.Ui`) run inside BWM's Retro bar (`modules/ii/bar/omarchy/`).

BWM changes, kept minimal so the files can be refreshed from upstream:
- `Commons/Color.qml`: `currentThemePath` is `~/.local/state/bwm/omarchy` (BWM's Omarchy
  palette: `colors.toml` + `shell.toml`, written by `hypr/scripts/bwm_omarchy.py`).
- `Commons/Style.qml`: `bwmScale` multiplies the font base size (and with it bar tokens and
  spacing); the Retro bar sets it to its height / 24.
- `Commons/I18n.qml`: without `OMARCHY_PATH`, strings come from `Commons/omarchy/default/i18n`
  (Omarchy's `default/i18n/{en,es}/shell.json` and `locales.json`).
