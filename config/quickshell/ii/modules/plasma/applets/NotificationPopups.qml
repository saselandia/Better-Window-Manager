// BWM: Plasma notification components on layer-shell; services/Notifications remains the only server.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import qs
import qs.modules.common
import qs.services
// BWM: initialize Plasma's KSvg image set even in an isolated popup host.
import org.kde.plasma.core as PlasmaCore
import org.kde.ksvg as KSvg
import "notifications"
Scope {
    id:root
    property var backend:Notifications
    readonly property alias popupWindow:toastWindow
    readonly property alias renderItem:list
    PanelWindow {
        id:toastWindow
        screen:Quickshell.screens.find(s=>Config.options.notifications.forceMonitor.enable?s.name===Config.options.notifications.forceMonitor.name:s.name===Hyprland.focusedMonitor?.name)??Quickshell.screens[0]
        visible:root.backend.popupList.length>0&&!GlobalStates.screenLocked
        anchors.top:true;anchors.right:true
        margins.top:16;margins.right:16
        implicitWidth:400;implicitHeight:list.implicitHeight
        color:"transparent";exclusionMode:ExclusionMode.Ignore
        WlrLayershell.namespace:"quickshell:plasmaNotifications"
        WlrLayershell.layer:WlrLayer.Overlay
        ColumnLayout {
            id:list
            anchors.fill:parent
            spacing:8
            Repeater {
                model:root.backend.popupList.slice(-3)
                delegate:Item {
                    id:toast
                    required property var modelData
                    Layout.fillWidth:true;implicitHeight:card.implicitHeight+12
                    KSvg.FrameSvgItem { anchors.fill:parent;imagePath:"solid/dialogs/background";prefix:"" }
                    NotificationCard {
                        id:card
                        anchors { left:parent.left;right:parent.right;margins:6 }
                        notification:toast.modelData;backend:root.backend
                    }
                    HoverHandler {
                        onHoveredChanged: {
                            if(hovered)root.backend.cancelTimeout(toast.modelData.notificationId);
                            else if(toast.modelData.notification?.expireTimeout!==0)dismiss.restart();
                        }
                    }
                    Timer { id:dismiss;interval:5000;onTriggered:root.backend.timeoutNotification(toast.modelData.notificationId) }
                }
            }
        }
    }
}
