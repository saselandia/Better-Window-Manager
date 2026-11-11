//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
//@ pragma Env QT_QUICK_FLICKABLE_WHEEL_DECELERATION=10000

// Breeze (Kde plasma) «System Settings» (fase 11 de docs/BREEZE_PLAN.md). Sidebar ported from
// systemsettings 6.7.5 (modules/plasma/settings: categories, search, «Highlight Changed
// Settings»), real Plasma KCMs embedded with org.bwm.kcm (src/bwm-kcmhost) and BWM's common pages
// for what every skin shares. Its own process: open-settings.sh sets QML_IMPORT_PATH and the
// org.kde.desktop style; launch with it (SETTINGS_PAGE=<id|name> or its first argument).

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import Quickshell
import org.kde.kirigami as Kirigami
import qs.services
import qs.modules.common
import qs.modules.plasma.theme
import "modules/plasma/settings"

QQC2.ApplicationWindow {
    id: root
    visible: true
    onClosing: Qt.quit()
    title: SettingsState.spanish ? "Preferencias del sistema" : "System Settings"
    minimumWidth: Kirigami.Units.gridUnit * 40
    minimumHeight: Kirigami.Units.gridUnit * 28
    width: Kirigami.Units.gridUnit * 64
    height: Kirigami.Units.gridUnit * 42
    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    color: Kirigami.Theme.backgroundColor

    Component.onCompleted: {
        // BWM's common pages keep their own widgets: give them the Breeze palette, radii and font
        // (only in this process, the shell is untouched), as the previous plasmaSettings.qml did.
        MaterialThemeLoader.forceBreeze = true;
        Appearance.rounding.unsharpen = 1;
        Appearance.rounding.unsharpenmore = 2;
        Appearance.rounding.verysmall = 3;
        Appearance.rounding.small = 4;
        Appearance.rounding.normal = 5;
        Appearance.rounding.large = 6;
        Appearance.rounding.verylarge = 8;
        Appearance.rounding.windowRounding = 8;
        for (const f of ["main", "title", "numbers", "reading", "expressive"])
            Appearance.font.family[f] = PlasmaTheme.fontMain;
        Config.readWriteDelay = 0; // one option at a time
        if (!SettingsState.openPage(Quickshell.env("SETTINGS_PAGE")))
            SettingsState.select("globaltheme", true);
    }

    Shortcut { sequence: StandardKey.Find; onActivated: sidebar.forceActiveFocus() }
    Shortcut { sequence: StandardKey.Quit; onActivated: root.close() }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        Main {
            id: sidebar
            Layout.fillHeight: true
            Layout.preferredWidth: implicitWidth
        }
        ModuleView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            headerHeight: sidebar.headerHeight
        }
    }
}
