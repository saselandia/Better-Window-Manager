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
import qs.modules.ii.plasmaKickoff
import qs.modules.ii.screensaver
import qs.modules.ii.screenshotPreview
import qs.modules.ii.omarchyNotifications
import qs.modules.ii.plasmaBluetooth
import qs.modules.ii.plasmaNetwork
import qs.modules.ii.plasmaCalendar
import qs.modules.ii.plasmaNotifications
import qs.modules.ii.plasmaTaskMenu
import qs.modules.ii.plasmaAudio
import qs.modules.ii.plasmaThemePicker

Scope {
    PanelLoader { extraCondition: !Config.options.bar.vertical; component: Bar {} }
    PanelLoader { extraCondition: Boolean(Config.options.background?.enable); component: Background {} }
    PanelLoader { component: Cheatsheet {} }
    PanelLoader { extraCondition: Config.options.dock.enable; component: Dock {} }
    PanelLoader { component: Lock {} }
    PanelLoader { component: MediaControls {} }
    PanelLoader { component: NotificationPopup {} }
    PanelLoader { component: OnScreenDisplay {} }
    PanelLoader { component: OnScreenKeyboard {} }
    PanelLoader { component: Overlay {} }
    PanelLoader { component: Overview {} }
    PanelLoader { component: Polkit {} }
    PanelLoader { component: RegionSelector {} }
    PanelLoader { extraCondition: Appearance.isRetro; component: OmarchyScreenshotPreview {} }
    // Retro: Omarchy's notification daemon instead of BWM's (services/Notifications.qml)
    PanelLoader { extraCondition: Config.ready && Appearance.isRetro; component: OmarchyNotifications {} }
    PanelLoader { component: ScreenCorners {} }
    PanelLoader { component: ScreenTranslator {} }
    PanelLoader { component: SessionScreen {} }
    PanelLoader { component: SidebarLeft {} }
    PanelLoader { component: SidebarRight {} }
    PanelLoader { extraCondition: Config.options.bar.vertical; component: VerticalBar {} }
    PanelLoader { component: WallpaperSelector {} }
    PanelLoader { component: AltTab {} }
    PanelLoader { component: OmarchyMenu {} }
    PanelLoader { component: PlasmaKickoff {} }
    PanelLoader { component: ScreensaverIdle {} }
    PanelLoader { component: PlasmaBluetooth {} }
    PanelLoader { component: PlasmaNetwork {} }
    PanelLoader { component: PlasmaTaskMenu {} }
    PanelLoader { component: PlasmaAudio {} }
    PanelLoader { component: PlasmaThemePicker {} }
    PanelLoader { component: PlasmaCalendar {} }
    PanelLoader { component: PlasmaNotifications {} }
}
