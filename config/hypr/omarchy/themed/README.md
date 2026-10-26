# Plantillas de apps del estilo Retro

Copiadas de Omarchy (`basecamp/omarchy`, rama `quattro`, `default/themed/*.tpl`, commit `c0b1088`,
licencia MIT, © David Heinemeier Hansson), salvo:

- `vesktop.theme.css.tpl`: propio de BWM (Omarchy no tematiza Discord).
- `btop.theme.tpl`, `kitty.conf.tpl`, `shell.toml.tpl`: versiones anteriores de las de Omarchy, ya integradas en BWM.

`bwm_omarchy_apps.render_theme_dir()` las rellena con la paleta del tema Retro en
`~/.local/state/bwm/omarchy/theme` (enlazado como `~/.local/state/omarchy/current/theme`) y
`apply_apps()` hace lo de cada `omarchy-theme-set-<app>`. Sintaxis: `{{ clave }}`, `{{ clave_strip }}`,
`{{ clave_rgb }}`, `{{ mix a b N% }}`, `{{ shell_gradient clave reserva }}` (`bwm_omarchy.render_omarchy`).
