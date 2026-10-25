# Preinstalled Omarchy bar plugins (Retro theme)

Copies of Omarchy shell plugins (all MIT, each folder keeps its `LICENSE`), loaded by the Retro
bar through `modules/ii/bar/omarchy/` with Omarchy's `qs.Commons` / `qs.Ui` (`../Commons`, `../Ui`).
They are enabled by default; Settings → Bar (Retro) turns each one off
(`~/.config/bwm/omarchy-plugins.json`, `hypr/scripts/bwm-plugin.sh enable|disable`).
More plugins: `bwm-plugin.sh add <git-url>` (installed under `~/.local/share/bwm/omarchy-plugins`).

| Folder | Plugin id | Source (commit) |
| :--- | :--- | :--- |
| `omarchy-clock` | `omarchy.clock` | basecamp/omarchy `shell/plugins/panels/clock` (4fa93e9f) — the clock and its calendar dropdown |
| `ai-usagebar` | `akitaonrails.ai-usagebar` | akitaonrails/ai-usagebar (d1af986f) — only `manifest.json` + the `omarchy/` frontend; the `ai-usagebar` binary is built by `bwm-plugin.sh build` (cargo, pinned to that commit) |
| `omastats` | `crmne.omastats` | crmne/omastats (5a3ddeea) — without the prebuilt `bin/` samplers: `sampler.py` runs in Python (or a local `cargo build` in `sampler/`) |
| `omarchy-mpris` | `crmne.mpris` | crmne/omarchy-mpris (411abaee) |
| `omarchy-active-window` | `crmne.active-window` | crmne/omarchy-active-window (da4e93b5) |

Left out from upstream: `.git`, tests, tools/scripts, preview images and agent notes.
Omarchy commands some plugins run (`omarchy-launch-floating-terminal-with-presentation`, …) are
provided by `hypr/scripts/omarchy-shims/`.
