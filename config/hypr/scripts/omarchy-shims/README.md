Stand-ins for the Omarchy commands that Omarchy bar plugins run through `bar.run(...)`.
The Retro bar's plugin host (`quickshell/ii/modules/ii/bar/omarchy/OmarchyPluginSlot.qml`) puts this
folder first in `PATH` for those commands only, and `bwm-plugin.sh catalog` links them into `~/.local/bin`
(never over an existing file) for the plugins that run them directly (weather, Elsewhen).
`omarchy-weather-*` are Omarchy's own scripts (MIT), with BWM's city (`bar.weather.city`) and units.
