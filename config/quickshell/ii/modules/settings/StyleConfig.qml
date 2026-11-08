import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.settings.shared

// "Estilo" page: Omarchy features shared by the three skins
//  * system monospace font (font-set.sh, port of omarchy-font-set): terminals, fontconfig's
//    "monospace" (Qt, GTK, Quickshell), GNOME's monospace font, Retro's TUI overlays
//  * glass mode (GlassModeSection; in General for default (end-4))
//  * inactividad común: pantallas o salvapantallas (Retro), bloqueo y suspensión (modules/ii/idle)
//  * boot splash / login screen matching the theme (bwm_boot.py, install-boot-theme.sh)
ContentPage {
    id: page
    forceWidth: true

    readonly property string scripts: Quickshell.env("HOME") + "/.config/hypr/scripts/"
    readonly property string script: scripts + "font-set.sh"
    property var fonts: []
    property string current: ""

    function refresh() {
        listProc.running = true;
        currentProc.running = true;
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

    // default (end-4) has it in General, like its other shell options
    GlassModeSection {
        visible: Appearance.isRetro || Appearance.isPlasma
    }

    // Inactividad (modules/ii/idle/BwmIdle.qml): los mismos tiempos en todas las skins; default
    // (end-4) y Breeze apagan las pantallas y Retro pone su salvapantallas (o también las apaga)
    ContentSection {
        icon: "bedtime"
        title: "Inactividad"

        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
            text: "Segundos sin usar el equipo; 0 = nunca. Son los mismos en todas las skins."
        }
        ConfigSwitch {
            visible: Appearance.isRetro
            buttonIcon: "terminal"
            text: "Salvapantallas de terminal (si no, se apagan las pantallas)"
            checked: Config.options.idle.screensaver
            onCheckedChanged: Config.options.idle.screensaver = checked
        }
        ConfigSpinBox {
            icon: Appearance.isRetro && Config.options.idle.screensaver ? "terminal" : "monitor"
            text: Appearance.isRetro && Config.options.idle.screensaver ? "Salvapantallas tras" : "Apagar las pantallas tras"
            value: Config.options.idle.screen
            from: 0
            to: 7200
            stepSize: 30
            onValueChanged: Config.options.idle.screen = value
        }
        ConfigSpinBox {
            icon: "lock"
            text: "Bloquear tras"
            value: Config.options.idle.lock
            from: 0
            to: 7200
            stepSize: 30
            onValueChanged: Config.options.idle.lock = value
        }
        ConfigSpinBox {
            icon: "bedtime"
            text: "Suspender tras"
            value: Config.options.idle.suspend
            from: 0
            to: 14400
            stepSize: 60
            onValueChanged: Config.options.idle.suspend = value
        }
        RippleButtonWithIcon {
            visible: Appearance.isRetro
            materialIcon: "play_arrow"
            mainText: "Probar el salvapantallas (cualquier tecla o el ratón lo cierran)"
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
