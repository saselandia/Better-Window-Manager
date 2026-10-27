import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets

// "Estilo" page: Omarchy features shared by the three skins
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

    function refresh() {
        listProc.running = true;
        currentProc.running = true;
        glassProc.running = true;
    }
    Component.onCompleted: refresh()

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
            text: "Fuente monoespaciada para los terminales, las apps que piden «monospace» y el aspecto TUI del estilo Retro. Se comparte entre los tres estilos."
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
                text: "Como el modo glass de Omarchy: terminales al 65 %, apps GTK atenuadas y\nbarra y menús con desenfoque esmerilado detrás. Para los tres estilos."
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
            text: "Pantalla de inicio de sesión (SDDM, en un Hyprland mínimo como en Omarchy) y de arranque (Plymouth) con el logo de BWM y los colores del estilo activo. Se regeneran solas al cambiar de fondo, de estilo o de tema. Instalarlas necesita root, una sola vez, en una terminal:\n  sudo ~/.config/hypr/scripts/install-boot-theme.sh --all            (SDDM + actualización automática)\n  sudo ~/.config/hypr/scripts/install-boot-theme.sh --plymouth       (pantalla de arranque)\n  sudo ~/.config/hypr/scripts/install-boot-theme.sh --disable-sddm   (volver al autologin)\n  sudo ~/.config/hypr/scripts/install-boot-theme.sh --revert         (quitar la pantalla de arranque)"
        }
        RippleButtonWithIcon {
            materialIcon: "palette"
            mainText: "Generar con los colores actuales"
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

}
