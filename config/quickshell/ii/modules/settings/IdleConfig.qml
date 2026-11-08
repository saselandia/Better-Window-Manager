import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.modules.common
import qs.modules.common.widgets

// "Inactividad": qué pasa al dejar de usar el equipo (modules/ii/idle/BwmIdle.qml). Los tiempos son
// los mismos en todas las skins (sección idle, común); el salvapantallas sólo existe en las skins que
// lo traen (Retro, como Omarchy)
ContentPage {
    id: page
    forceWidth: true

    readonly property bool hasScreensaver: Appearance.isRetro

    // Un tiempo en minutos y segundos (se guarda en segundos; 0 + 0 = nunca)
    component DurationRow: RowLayout {
        id: row
        property string text: ""
        property string icon: ""
        property int value: 0
        property int max: 7200
        signal edited(int seconds)
        spacing: 10
        Layout.leftMargin: 8
        Layout.rightMargin: 8

        OptionalMaterialSymbol {
            icon: row.icon
            opacity: row.enabled ? 1 : 0.4
        }
        StyledText {
            Layout.fillWidth: true
            text: row.text
            color: Appearance.colors.colOnSecondaryContainer
            opacity: row.enabled ? 1 : 0.4
        }
        StyledText {
            visible: row.value <= 0
            text: "Nunca"
            color: Appearance.colors.colSubtext
        }
        StyledSpinBox {
            from: 0
            to: Math.floor(row.max / 60)
            value: Math.floor(row.value / 60)
            onValueChanged: {
                const total = Math.min(row.max, value * 60 + row.value % 60);
                if (total !== row.value) row.edited(total);
            }
        }
        StyledText { text: "min"; color: Appearance.colors.colSubtext }
        StyledSpinBox {
            from: 0
            to: 59
            stepSize: 5
            value: row.value % 60
            onValueChanged: {
                const total = Math.min(row.max, Math.floor(row.value / 60) * 60 + value);
                if (total !== row.value) row.edited(total);
            }
        }
        StyledText { text: "s"; color: Appearance.colors.colSubtext }
    }

    StyledText {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        color: Appearance.colors.colSubtext
        text: "Tiempo sin tocar el teclado ni el ratón; 0 min 0 s = nunca. Es el mismo en todas las skins. «Mantener despierto» y las apps que lo piden (vídeo a pantalla completa, juegos) lo detienen."
    }

    ContentSection {
        visible: page.hasScreensaver
        icon: "terminal"
        title: "Salvapantallas"

        ConfigSwitch {
            buttonIcon: "terminal"
            text: "Salvapantallas de terminal"
            checked: Config.options.idle.screensaver
            onCheckedChanged: Config.options.idle.screensaver = checked
        }
        DurationRow {
            enabled: Config.options.idle.screensaver
            icon: "timer"
            text: "Mostrar tras"
            value: Config.options.idle.screensaverTime
            max: 7200
            onEdited: seconds => Config.options.idle.screensaverTime = seconds
        }
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
            text: "No sale con música o vídeo sonando. Si las pantallas se apagan antes, no llega a verse."
        }
        RippleButtonWithIcon {
            materialIcon: "play_arrow"
            mainText: "Probar (cualquier tecla o el ratón lo cierran)"
            onClicked: Quickshell.execDetached(["qs", "-c", "ii", "ipc", "call", "screensaver", "start"])
        }
    }

    ContentSection {
        icon: "monitor"
        title: "Pantallas"

        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
            text: "Sólo se apagan los monitores: el equipo sigue funcionando (música, descargas, juegos y apps abiertas). Vuelven al mover el ratón o pulsar una tecla."
        }

        DurationRow {
            icon: "desktop_access_disabled"
            text: "Apagar los monitores tras"
            value: Config.options.idle.screen
            max: 7200
            onEdited: seconds => Config.options.idle.screen = seconds
        }
    }

    ContentSection {
        icon: "lock"
        title: "Bloqueo y suspensión"

        DurationRow {
            icon: "lock"
            text: "Bloquear tras"
            value: Config.options.idle.lock
            max: 7200
            onEdited: seconds => Config.options.idle.lock = seconds
        }
        DurationRow {
            icon: "bedtime"
            text: "Suspender tras"
            value: Config.options.idle.suspend
            max: 14400
            onEdited: seconds => Config.options.idle.suspend = seconds
        }
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
            text: "Suspender duerme el equipo entero: se para todo (procesador, tarjeta gráfica, discos, ventiladores) y gasta casi nada, pero también se detienen la música, las descargas y lo que esté haciendo. Se despierta con una tecla o el botón de encendido, con las apps como estaban. Apagado por defecto (0 = nunca)."
        }
    }
}
