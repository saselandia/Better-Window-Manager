# Preinstalled third-party Omarchy bar plugins (Retro theme)

Copies of community Omarchy shell plugins (all MIT, each folder keeps its `LICENSE`). Retro's bar is
Omarchy's own (`../omarchyShell`, its host and first-party plugins), which reads this folder like the
plugins a user installs in `~/.config/omarchy/plugins` (`omarchyShell/services/PluginRegistry.qml`,
`bundledPluginsDir`); a plugin of the same id there wins. They go on the bar, or off it, like any other
Omarchy plugin: `omarchy plugin enable|disable <id>`, Settings → Plugins, or by editing
`~/.config/omarchy/shell.json`. More plugins: `omarchy plugin add <git-url>` (or `bwm-plugin.sh add`).

| Folder | Plugin id | Source (commit) |
| :--- | :--- | :--- |
| `ai-usagebar` | `akitaonrails.ai-usagebar` | akitaonrails/ai-usagebar (d1af986f) — only `manifest.json` + the `omarchy/` frontend; the `ai-usagebar` binary is built by `bwm-plugin.sh build` (cargo, pinned to that commit) |
| `omastats` | `crmne.omastats` | crmne/omastats (5a3ddeea) — without the prebuilt `bin/` samplers: `sampler.py` runs in Python (or a local `cargo build` in `sampler/`) |
| `omarchy-mpris` | `crmne.mpris` | crmne/omarchy-mpris (411abaee) |
| `omarchy-active-window` | `crmne.active-window` | crmne/omarchy-active-window (da4e93b5) |

Omarchy's own widgets (clock, weather, Elsewhen, audio, network…) are first-party plugins of its
shell, in `../omarchyShell/plugins` (basecamp/omarchy quattro 18ac93c).

BWM changes to `omarchy-mpris`: `NowPlayingPanel.qml` (left click: now-playing dropdown with art,
seekable progress, shuffle/repeat and player chips; IPC `bwm.nowPlaying toggle`) and a
`bwmWidthBudget` hook in `BarGeometry.js`, which Omarchy's bar does not set (the plugin then sizes
itself as upstream).

Left out from upstream: `.git`, tests, tools/scripts, preview images and agent notes.
Omarchy commands some plugins run (`omarchy-launch-floating-terminal-with-presentation`, …) are
provided by `hypr/scripts/omarchy-shims/`.
