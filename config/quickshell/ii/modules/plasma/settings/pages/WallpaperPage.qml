// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import Quickshell
import org.kde.kirigami as Kirigami
import qs.modules.common
import ".."

/**
 * BWM F11: wallpaper of Breeze. Plasma's kcm_wallpaper configures plasmashell over D-Bus, which
 * BWM does not run, and the common BackgroundConfig only has end-4's background widgets. The
 * wallpaper is per skin (rule 14) and Breeze sets it with the common set-wallpaper.sh: this page
 * shows the current one and opens Breeze's picker (wallpaper-picker.sh, Alt+W).
 */
Item {
    id: page
    property var entry
    function t(en, es) { return SettingsState.spanish ? es : en; }
    readonly property string path: Config.options.background?.wallpaperPath ?? ""

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - Kirigami.Units.gridUnit * 4, Kirigami.Units.gridUnit * 36)
        spacing: Kirigami.Units.largeSpacing

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: width * 9 / 16
            color: Kirigami.Theme.alternateBackgroundColor
            border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
            radius: Kirigami.Units.cornerRadius
            clip: true
            Image {
                anchors.fill: parent
                anchors.margins: 1
                source: page.path ? "file://" + page.path : ""
                sourceSize.width: 1280
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
            }
        }
        QQC2.Label {
            Layout.fillWidth: true
            text: page.path || page.t("No wallpaper set", "Sin fondo")
            elide: Text.ElideMiddle
            horizontalAlignment: Text.AlignHCenter
            opacity: 0.7
        }
        QQC2.Button {
            Layout.alignment: Qt.AlignHCenter
            icon.name: "preferences-desktop-wallpaper"
            text: page.t("Choose Wallpaper…", "Elegir fondo…")
            onClicked: Quickshell.execDetached([Quickshell.env("HOME") + "/.config/hypr/scripts/wallpaper-picker.sh"])
        }
    }
}
