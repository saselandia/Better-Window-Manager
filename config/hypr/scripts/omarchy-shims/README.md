Omarchy commands (`omarchy-*`) for BWM: copies of Omarchy's own `bin/` scripts (MIT, most unchanged) and
BWM stand-ins where Omarchy's would act on Arch, its own state or root. Retro's bar is Omarchy's
(`quickshell/ii/omarchyShell`), which runs them by name; `bwm-plugin.sh catalog` links them into
`~/.local/bin` (never over an existing file), which is in the shell's `PATH`. `$OMARCHY_PATH/bin`
(`config/hypr/omarchy/bin`) is a link to this folder too, as Omarchy's scripts expect.
`omarchy-weather-*` are Omarchy's own scripts (MIT), with BWM's city (`bar.weather.city`) and units.
