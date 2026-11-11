import QtQuick
import Quickshell

import qs.modules.common
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
import qs.modules.ii.plasmaTaskMenu
import qs.modules.ii.plasmaThemePicker

Scope {
    // Retro: Omarchy's own bar, inside omarchy-shell's host (omarchyShell/), with its panels and plugins
    PanelLoader { extraCondition: !Config.options.bar.vertical && !Appearance.isRetro && !Appearance.isPlasma; component: Bar {} }
    PanelLoader { extraCondition: Appearance.isRetro; component: OmarchyShell {} }
    // The source is empty outside Breeze: its KDE QML dependencies remain skin-specific.
    PanelLoader {
        extraCondition: Appearance.isPlasma
        source: extraCondition ? Qt.resolvedUrl("../modules/plasma/panel/Panel.qml") : ""
    }
    // Fondo pintado por el shell, como en el original: el de end-4 en default (end-4) y el de
    // Omarchy (con su transición) en Retro; Breeze sigue con swww salvo background.enable
    PanelLoader { extraCondition: (!Appearance.isRetro && !Appearance.isPlasma) || (Appearance.isPlasma && Boolean(Config.options.background?.enable)); component: Background {} }
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
    PanelLoader { extraCondition: !Appearance.isRetro; component: Polkit {} }
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
    PanelLoader { component: SessionScreen {} }
    PanelLoader { component: SidebarLeft {} }
    PanelLoader { component: SidebarRight {} }
    PanelLoader { extraCondition: Config.options.bar.vertical && !Appearance.isRetro && !Appearance.isPlasma; component: VerticalBar {} }
    PanelLoader { component: WallpaperSelector {} }
    PanelLoader { component: AltTab {} }
    PanelLoader { component: OmarchyMenu {} }
    PanelLoader { extraCondition: Appearance.isPlasma; component: PlasmaKickoffPort.KickoffWindow {} } // F4: Kickoff de Plasma 6.7.5 portado
    PanelLoader { component: BwmIdle {} }
    // F5: KDE applet interfaces, BWM data/services; no Plasma notification server.
    PanelLoader { extraCondition:Appearance.isPlasma; source:extraCondition?Qt.resolvedUrl("../modules/plasma/tray/TrayController.qml"):"" }
    PanelLoader { extraCondition:Appearance.isPlasma; source:extraCondition?Qt.resolvedUrl("../modules/plasma/applets/NotificationPopups.qml"):"" }
    PanelLoader { component: PlasmaTaskMenu {} }
    PanelLoader { component: PlasmaThemePicker {} }
}
