import qs.modules.common
import qs.services
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
pragma Singleton
pragma ComponentBehavior: Bound

Singleton {
    id: root
    property bool barOpen: true
    property bool crosshairOpen: false
    property bool sidebarLeftOpen: false
    property bool sidebarRightOpen: false
    property bool mediaControlsOpen: false
    property bool osdBrightnessOpen: false
    property bool osdVolumeOpen: false
    property bool oskOpen: false
    property bool overlayOpen: false
    property bool overviewOpen: false
    property bool regionSelectorOpen: false
    property bool searchOpen: false
    property bool screenLocked: false
    property bool screenLockContainsCharacters: false
    property bool screenUnlockFailed: false
    property bool screenTranslatorOpen: false
    property bool sessionOpen: false
    property bool superDown: false
    property bool superReleaseMightTrigger: true
    property bool wallpaperSelectorOpen: false
    property bool workspaceShowNumbers: false
    // KDE Plasma Bluetooth applet (opened from the Plasma taskbar)
    property bool plasmaBluetoothOpen: false
    property real plasmaBluetoothAnchorX: -1
    property string plasmaBluetoothScreen: ""
    // KDE Plasma Networks applet (opened from the Plasma taskbar)
    property bool plasmaNetworkOpen: false
    property real plasmaNetworkAnchorX: -1
    property string plasmaNetworkScreen: ""
    // KDE Plasma audio applet (opened from the Plasma taskbar volume button)
    property bool plasmaAudioOpen: false
    property real plasmaAudioAnchorX: -1
    property string plasmaAudioScreen: ""
    // KDE Plasma global theme picker (opened from the Plasma taskbar palette button)
    property bool plasmaThemePickerOpen: false
    property real plasmaThemePickerAnchorX: -1
    property string plasmaThemePickerScreen: ""
    // KDE Plasma task manager: right-click menu, hover window list and window peek
    property bool plasmaTaskMenuOpen: false
    property real plasmaTaskMenuAnchorX: -1
    property string plasmaTaskMenuScreen: ""
    property string plasmaTaskMenuApp: ""
    property string plasmaTaskHoverApp: ""
    property real plasmaTaskHoverX: -1
    property string plasmaTaskHoverScreen: ""
    property string plasmaTaskPeek: ""   // Hyprland address (no 0x) of the window being peeked
    // KDE Plasma notifications applet (opened from the bell in the Plasma taskbar tray)
    property bool plasmaNotificationsOpen: false
    property real plasmaNotificationsAnchorX: -1
    property string plasmaNotificationsScreen: ""
    // KDE Plasma digital clock calendar (opened from the Plasma taskbar clock)
    property bool plasmaCalendarOpen: false
    property real plasmaCalendarAnchorX: -1
    property string plasmaCalendarScreen: ""

    onSidebarRightOpenChanged: {
        if (GlobalStates.sidebarRightOpen) {
            Notifications.timeoutAll();
            Notifications.markAllRead();
        }
    }

    GlobalShortcut {
        name: "workspaceNumber"
        description: "Hold to show workspace numbers, release to show icons"

        onPressed: {
            root.superDown = true
        }
        onReleased: {
            root.superDown = false
        }
    }
}