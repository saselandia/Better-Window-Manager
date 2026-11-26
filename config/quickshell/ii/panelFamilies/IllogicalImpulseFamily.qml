import QtQuick
import Quickshell
import Quickshell.Io

import qs.modules.common
import qs.modules.common.functions
import qs.services
import qs.modules.ii.background
import qs.modules.ii.bar
import qs.modules.ii.cheatsheet
import qs.modules.ii.dock
import qs.modules.ii.lock
import qs.modules.ii.mediaControls
import qs.modules.ii.notificationPopup
import qs.modules.ii.onScreenDisplay
import qs.modules.ii.onScreenKeyboard
import qs.modules.ii.overview
import qs.modules.ii.polkit
import qs.modules.ii.omarchyPolkit
import qs.modules.ii.omarchyBackground
// Named import: omarchyDock also has a Dock.qml, which would otherwise shadow end-4's Dock below
import qs.modules.ii.omarchyDock as OmarchyDockModule
import qs.modules.ii.regionSelector
import qs.modules.ii.screenCorners
import qs.modules.ii.screenTranslator
import qs.modules.ii.sessionScreen
import qs.modules.ii.sidebarLeft
import qs.modules.ii.sidebarRight
import qs.modules.ii.overlay
import qs.modules.ii.verticalBar
import qs.modules.ii.wallpaperSelector
import qs.modules.ii.altTab
import qs.modules.ii.omarchyMenu
import qs.modules.plasma.kickoff as PlasmaKickoffPort
import qs.modules.ii.idle
import qs.modules.ii.screenshotPreview
import qs.modules.ii.omarchyNotifications
import qs.omarchyShell

Scope {
    id: familyRoot
    // R4–R5: while native bwm-plasma-host (--session) is running, it owns the Plasma panel,
    // Kickoff, System Tray, Notifications and DesktopEditMode; Quickshell keeps the fallback ready if it stops.
    property bool _nativeHostReady: false
    readonly property bool nativePlasmaHost: Appearance.isPlasma && _nativeHostReady && (Config.options?.bar?.plasma?.nativeHost ?? true)
    readonly property string _nativeHostHelper: FileUtils.trimFileProtocol(Quickshell.shellPath("../..")) + "/hypr/skins/plasma/scripts/plasma-host.py"
    Process {
        id: nativeHostProbe
        command: ["python3", familyRoot._nativeHostHelper, "ready"]
        property bool receivedResult: false
        function check() {
            if (running) return;
            // FailedToStart may only emit runningChanged(false), without ever
            // announcing true. Clear the previous result before requesting start.
            receivedResult = false;
            running = true;
        }
        onExited: exitCode => {
            receivedResult = true;
            const ready = (exitCode === 0);
            familyRoot._nativeHostReady = ready;
            Notifications.updateNativeHostReady(ready);
        }
        onRunningChanged: {
            if (running) receivedResult = false;
            else if (!receivedResult) {
                familyRoot._nativeHostReady = false;
                Notifications.updateNativeHostReady(false);
            }
        }
    }
    Timer {
        interval: 1500
        repeat: true
        running: Appearance.isPlasma
        triggeredOnStart: true
        onTriggered: nativeHostProbe.check()
    }

    // Retro: Omarchy's own bar, inside omarchy-shell's host (omarchyShell/), with its panels and plugins
    PanelLoader { extraCondition: !Config.options.bar.vertical && !Appearance.isRetro && !Appearance.isPlasma; component: Bar {} }
    PanelLoader { extraCondition: Appearance.isRetro; component: OmarchyShell {} }
    // The source is empty outside Breeze: its KDE QML dependencies remain skin-specific.
    PanelLoader {
        extraCondition: Appearance.isPlasma && !familyRoot.nativePlasmaHost
        source: extraCondition ? Qt.resolvedUrl("../modules/plasma/panel/Panel.qml") : ""
    }
    // Fondo pintado por el shell, como en el original: el de end-4 en default (end-4) y el de
    // Omarchy (con su transición) en Retro; Breeze sigue con swww salvo background.enable
    PanelLoader { extraCondition: (!Appearance.isRetro && !Appearance.isPlasma) || (Appearance.isPlasma && !familyRoot.nativePlasmaHost && Boolean(Config.options.background?.enable)); component: Background {} }
    PanelLoader { extraCondition: Appearance.isRetro; component: OmarchyBackground {} }
    PanelLoader { extraCondition: !Appearance.isRetro; component: Cheatsheet {} }
    // BWM's dock; Retro has Omarchy's instead (dock.omarchy), never both
    PanelLoader { extraCondition: Config.options.dock.enable && !Appearance.isRetro; component: Dock {} }
    PanelLoader { component: Lock {} }
    PanelLoader { component: MediaControls {} }
    PanelLoader { extraCondition: !Appearance.isRetro && !Appearance.isPlasma; component: NotificationPopup {} }
    PanelLoader { component: OnScreenDisplay {} }
    PanelLoader { component: OnScreenKeyboard {} }
    PanelLoader { component: Overlay {} }
    PanelLoader { component: Overview {} }
    PanelLoader { extraCondition: !Appearance.isRetro && !Appearance.isPlasma; component: Polkit {} }
    // Retro: Omarchy's polkit dialog (BWM's agent in services/PolkitService.qml is off there)
    PanelLoader { extraCondition: Config.ready && Appearance.isRetro; component: OmarchyPolkit {} }
    // Retro: Omarchy's dock, on workspaces without tiled windows (modules/ii/omarchyDock); optional,
    // Settings → Interface → Dock
    PanelLoader { extraCondition: Config.ready && Appearance.isRetro && Config.options.dock.omarchy; component: OmarchyDockModule.OmarchyDock {} }
    PanelLoader { component: RegionSelector {} }
    PanelLoader { extraCondition: Appearance.isRetro; component: OmarchyScreenshotPreview {} }
    // Retro: Omarchy's notification daemon instead of BWM's (services/Notifications.qml)
    PanelLoader { extraCondition: Config.ready && Appearance.isRetro; component: OmarchyNotifications {} }
    PanelLoader { component: ScreenCorners {} }
    PanelLoader { component: ScreenTranslator {} }
    PanelLoader { extraCondition: !Appearance.isPlasma; component: SessionScreen {} }
    PanelLoader { extraCondition: Appearance.isPlasma; source: extraCondition ? Qt.resolvedUrl("../modules/plasma/session/SessionScreen.qml") : "" }
    PanelLoader { component: SidebarLeft {} }
    PanelLoader { component: SidebarRight {} }
    PanelLoader { extraCondition: Config.options.bar.vertical && !Appearance.isRetro && !Appearance.isPlasma; component: VerticalBar {} }
    PanelLoader { component: WallpaperSelector {} }
    PanelLoader { component: AltTab {} }
    PanelLoader { component: OmarchyMenu {} }
    PanelLoader { extraCondition: Appearance.isPlasma && !familyRoot.nativePlasmaHost; component: PlasmaKickoffPort.KickoffWindow {} } // F4: Kickoff de Plasma 6.7.5 portado
    PanelLoader { component: BwmIdle {} }
    // F5 fallback: KDE applet interfaces over Quickshell's server; off while native host owns notifications.
    PanelLoader { extraCondition: Appearance.isPlasma && !familyRoot.nativePlasmaHost; source: extraCondition ? Qt.resolvedUrl("../modules/plasma/tray/TrayController.qml") : "" }
    PanelLoader { extraCondition: Appearance.isPlasma && !familyRoot.nativePlasmaHost; source: extraCondition ? Qt.resolvedUrl("../modules/plasma/applets/NotificationPopups.qml") : "" }
    // F9: menús contextuales de Plasma (ventana, tareas, escritorio, panel) y el clic derecho en el fondo
    PanelLoader { extraCondition: Appearance.isPlasma; source: extraCondition ? Qt.resolvedUrl("../modules/plasma/menus/MenuHost.qml") : "" }
    PanelLoader { extraCondition: Appearance.isPlasma && !familyRoot.nativePlasmaHost; source: extraCondition ? Qt.resolvedUrl("../modules/plasma/menus/DesktopCatcher.qml") : "" }
    PanelLoader { extraCondition: Appearance.isPlasma; source: extraCondition ? Qt.resolvedUrl("../modules/plasma/skinPicker/SkinPicker.qml") : "" }
    // F10: KSvg outline and KWin-format custom tiling editor, Breeze only.
    PanelLoader { extraCondition: Appearance.isPlasma; source: extraCondition ? Qt.resolvedUrl("../modules/plasma/tiling/Outline.qml") : "" }
    PanelLoader { extraCondition: Appearance.isPlasma; source: extraCondition ? Qt.resolvedUrl("../modules/plasma/tiling/TileEditor.qml") : "" }
}
