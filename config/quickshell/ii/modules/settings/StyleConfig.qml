import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets

// "Estilo" page: Omarchy features shared by the three themes
//  * system monospace font (font-set.sh, port of omarchy-font-set): terminals, fontconfig's
//    "monospace" (Qt, GTK, Quickshell), GNOME's monospace font, Retro's TUI overlays
//  * glass mode (glass.sh, port of Omarchy's glassy windows)
//  * terminal screensaver on idle (modules/ii/screensaver, launch-screensaver.sh)
//  * boot splash / login screen matching the theme (bwm_boot.py, install-boot-theme.sh)
ContentPage {
    id: page
    forceWidth: true

    readonly property string scripts: Quickshell.env("HOME") + "/.config/hypr/scripts/"
    readonly property string script: scripts + "font-set.sh"
    property bool glass: false
    property var fonts: []
    property string current: ""

    property string retroMode: "dynamic"
    property string retroThemeName: "dynamic"

    function refresh() {
        listProc.running = true;
        currentProc.running = true;
        glassProc.running = true;
        retroModeProc.running = true;
    }
    Component.onCompleted: refresh()

    Process {
        id: retroModeProc
        command: ["python3", page.scripts + "bwm_omarchy.py", "get-mode"]
        stdout: StdioCollector {
            onStreamFinished: {
                var parts = text.trim().split("\t");
                if (parts.length >= 2) {
                    page.retroMode = parts[0];
                    page.retroThemeName = parts[1];
                }
            }
        }
    }
    Process {
        id: listProc
        command: [page.script, "list"]
        stdout: StdioCollector {
            onStreamFinished: page.fonts = text.trim().split("\n").filter(f => f.length > 0)
        }
    }
    Process {
        id: currentProc
        command: [page.script, "current"]
        stdout: StdioCollector {
            onStreamFinished: page.current = text.trim()
        }
    }
    Process {
        id: setProc
        onExited: page.refresh()
    }
    Process {
        id: glassProc
        command: [page.scripts + "glass.sh", "status"]
        stdout: StdioCollector {
            onStreamFinished: page.glass = text.trim() === "on"
        }
    }
    Process {
        id: bootProc
        command: ["python3", page.scripts + "bwm_boot.py", "render"]
        stdout: StdioCollector {
            onStreamFinished: bootStatus.text = text.trim()
        }
    }

    ContentSection {
        icon: "font_download"
        title: "Fuente del sistema"

        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Appearance.colors.colSubtext
            text: "Fuente monoespaciada para los terminales, las apps que piden «monospace» y el aspecto TUI del tema Retro. Se comparte entre los tres temas."
        }

        ConfigSelectionArray {
            currentValue: page.current
            onSelected: newValue => {
                page.current = newValue;
                setProc.command = [page.script, "set", newValue];
                setProc.running = true;
            }
            options: page.fonts.map(f => ({ displayName: f, icon: "text_fields", value: f }))
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: preview.implicitHeight + 24
            radius: Appearance.rounding.small
            color: Appearance.colors.colLayer2

            Text {
                id: preview
                anchors.fill: parent
                anchors.margins: 12
                wrapMode: Text.Wrap
                color: Appearance.colors.colOnLayer2
                font.family: page.current
                font.pixelSize: 15
                text: "$ btop --theme omarchy\nThe quick brown fox jumps over the lazy dog 0123456789\n{ } [ ] ( ) => != <= >= == :: ->   "
            }
        }

        RippleButtonWithIcon {
            materialIcon: "refresh"
            mainText: "Buscar fuentes instaladas"
            onClicked: page.refresh()
        }
    }

    ContentSection {
        icon: "blur_on"
        title: "Modo glass"

        ConfigSwitch {
            buttonIcon: "opacity"
            text: "Ventanas translúcidas con desenfoque"
            checked: page.glass
            onClicked: {
                page.glass = !page.glass;
                Quickshell.execDetached([page.scripts + "glass.sh", page.glass ? "on" : "off"]);
            }
            StyledToolTip {
                text: "Como el modo glass de Omarchy: terminales al 65 %, apps GTK atenuadas y\nbarra y menús con desenfoque esmerilado detrás. Para los tres temas."
            }
        }
    }

    ContentSection {
        icon: "screenshot_monitor"
        title: "Salvapantallas"

        ConfigSwitch {
            buttonIcon: "terminal"
            text: "Salvapantallas de terminal al estar inactivo"
            checked: Config.options.screensaver.enable
            onCheckedChanged: Config.options.screensaver.enable = checked
        }
        ConfigSpinBox {
            enabled: Config.options.screensaver.enable
            icon: "timer"
            text: "Minutos de inactividad"
            value: Config.options.screensaver.timeoutMinutes
            from: 1
            to: 120
            stepSize: 1
            onValueChanged: Config.options.screensaver.timeoutMinutes = value
        }
        RippleButtonWithIcon {
            materialIcon: "play_arrow"
            mainText: "Probar ahora (cualquier tecla o el ratón lo cierran)"
            onClicked: Quickshell.execDetached(["qs", "-c", "ii", "ipc", "call", "screensaver", "start"])
        }
    }

    ContentSection {
        icon: "power_settings_new"
        title: "Arranque e inicio de sesión"

        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Appearance.colors.colSubtext
            text: "Pantalla de inicio de sesión (SDDM, en un Hyprland mínimo como en Omarchy) y de arranque (Plymouth) con el logo de BWM y los colores del tema activo. Se regeneran solas al cambiar de fondo o de tema. Instalarlas necesita root, una sola vez, en una terminal:\n  sudo ~/.config/hypr/scripts/install-boot-theme.sh --all            (SDDM + actualización automática)\n  sudo ~/.config/hypr/scripts/install-boot-theme.sh --plymouth       (pantalla de arranque)\n  sudo ~/.config/hypr/scripts/install-boot-theme.sh --disable-sddm   (volver al autologin)\n  sudo ~/.config/hypr/scripts/install-boot-theme.sh --revert         (quitar la pantalla de arranque)"
        }
        RippleButtonWithIcon {
            materialIcon: "palette"
            mainText: "Generar con los colores del tema actual"
            onClicked: bootProc.running = true
        }
        StyledText {
            id: bootStatus
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Appearance.colors.colSubtext
            text: ""
        }
    }

    ContentSection {
        icon: "palette"
        title: "Paleta Retro (Omarchy)"
        visible: Appearance.isRetro

        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Appearance.colors.colSubtext
            text: "Modo activo: " + (page.retroMode === "static" ? ("Tema estático oficial (" + page.retroThemeName + ")") : "Paleta dinámica desde el wallpaper") + ".\nPuedes alternar entre la paleta dinámica adaptada a tu wallpaper actual o uno de los 23 temas oficiales calibrados a mano de Omarchy."
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            RippleButtonWithIcon {
                materialIcon: "view_carousel"
                mainText: "Abrir galería visual 3D (Carrusel)"
                onClicked: Quickshell.execDetached(["omarchy-shell", "shell", "summon", "omarchy.image-picker", "{\"source\":\"themes\"}"])
            }

            RippleButtonWithIcon {
                materialIcon: "refresh"
                mainText: "Paleta dinámica (desde wallpaper)"
                onClicked: {
                    Quickshell.execDetached(["omarchy-theme-set", "dynamic"]);
                    page.refresh();
                }
            }
        }

        StyledText {
            Layout.fillWidth: true
            color: Appearance.colors.colSubtext
            font.bold: true
            text: "Temas oficiales destacados:"
        }

        Flow {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: [
                    { name: "Tokyo Night", id: "tokyo-night" },
                    { name: "Catppuccin Mocha", id: "catppuccin" },
                    { name: "Catppuccin Latte", id: "catppuccin-latte" },
                    { name: "Nord", id: "nord" },
                    { name: "Gruvbox", id: "gruvbox" },
                    { name: "Kanagawa", id: "kanagawa" },
                    { name: "Rose Pine", id: "rose-pine" },
                    { name: "Everforest", id: "everforest" },
                    { name: "Osaka Jade", id: "osaka-jade" },
                    { name: "Retro 82", id: "retro-82" },
                    { name: "Starship", id: "starship" },
                    { name: "Hackerman", id: "hackerman" },
                    { name: "Lumon", id: "lumon" }
                ]

                delegate: RippleButtonWithIcon {
                    materialIcon: "color_lens"
                    mainText: modelData.name
                    onClicked: {
                        Quickshell.execDetached(["omarchy-theme-set", modelData.id]);
                        page.refresh();
                    }
                }
            }
        }
    }
}
