// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import Quickshell
import org.kde.kirigami as Kirigami
import qs.modules.common
import ".."

/**
 * BWM F11: modules that have no embeddable QML KCM here (Wi-Fi & Internet is a QWidget KCM,
 * Bluetooth's KCM is not installed). They open the app BWM already uses for them
 * (Config.options.apps.network / .bluetooth, common to every skin): the tray applet stays the
 * quick way, as in Plasma.
 */
Item {
    id: page
    property var entry
    readonly property string command: entry && Config.options.apps ? (Config.options.apps[entry.app] ?? "") : ""

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 6
        icon.name: page.entry ? SettingsState.iconFor(page.entry) : ""
        text: page.entry ? SettingsState.label(page.entry) : ""
        explanation: SettingsState.spanish
            ? "Esta página se abre en su propia ventana con la aplicación configurada en BWM. Para lo habitual, usa el applet de la bandeja del panel."
            : "This page opens in its own window with the app configured in BWM. For everyday use, use the panel's tray applet."
        helpfulAction: Kirigami.Action {
            enabled: page.command.length > 0
            icon.name: "window-new"
            text: SettingsState.spanish ? "Abrir" : "Open"
            onTriggered: Quickshell.execDetached(["bash", "-c", page.command])
        }
    }
}
