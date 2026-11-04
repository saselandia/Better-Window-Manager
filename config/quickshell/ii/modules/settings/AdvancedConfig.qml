import QtQuick
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.functions

ContentPage {
    forceWidth: true

    // El modo neutro de la terminal se aplica al momento (sólo en default (end-4), dueña de esta paleta);
    // espera a que Config haya guardado el cambio
    Timer {
        id: reapplyTerminal
        interval: 800
        onTriggered: if (!Appearance.isRetro && !Appearance.isPlasma) applyTerminalProc.running = true
    }
    Process {
        id: applyTerminalProc
        command: ["bash", FileUtils.trimFileProtocol(Directories.config) + "/quickshell/ii/scripts/colors/applycolor.sh"]
    }

    ContentSection {
        icon: "colors"
        title: Translation.tr("Color generation")

        ConfigSwitch {
            buttonIcon: "tv_options_input_settings"
            text: Translation.tr("Qt apps")
            checked: Config.options.appearance.wallpaperTheming.enableQtApps
            onCheckedChanged: {
                Config.options.appearance.wallpaperTheming.enableQtApps = checked;
            }
        }
        ConfigRow {
            uniform: true
            ConfigSwitch {
                // BWM: sustituye a «Forzar modo oscuro en la terminal» (forceDarkMode se sigue leyendo)
                buttonIcon: "contrast"
                text: Translation.tr("Neutral terminal")
                checked: Config.options.appearance.wallpaperTheming.terminalGenerationProps.neutral
                onCheckedChanged: {
                    if (Config.options.appearance.wallpaperTheming.terminalGenerationProps.neutral === checked)
                        return;
                    Config.options.appearance.wallpaperTheming.terminalGenerationProps.neutral = checked;
                    reapplyTerminal.restart();
                }
                StyledToolTip {
                    text: Translation.tr("Fixed palette (end-4 base) that never changes with the wallpaper or theme")
                }
            }
        }

        ConfigSpinBox {
            icon: "invert_colors"
            enabled: !Config.options.appearance.wallpaperTheming.terminalGenerationProps.neutral
            text: Translation.tr("Terminal: Harmony (%)")
            value: Config.options.appearance.wallpaperTheming.terminalGenerationProps.harmony * 100
            from: 0
            to: 100
            stepSize: 10
            onValueChanged: {
                Config.options.appearance.wallpaperTheming.terminalGenerationProps.harmony = value / 100;
            }
        }
        ConfigSpinBox {
            icon: "format_color_text"
            enabled: !Config.options.appearance.wallpaperTheming.terminalGenerationProps.neutral
            text: Translation.tr("Terminal: Foreground boost (%)")
            value: Config.options.appearance.wallpaperTheming.terminalGenerationProps.termFgBoost * 100
            from: 0
            to: 100
            stepSize: 10
            onValueChanged: {
                Config.options.appearance.wallpaperTheming.terminalGenerationProps.termFgBoost = value / 100;
            }
        }
    }



}
