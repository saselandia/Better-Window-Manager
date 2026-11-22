// BWM: Plasma ToolTipDelegate's window list, using Quickshell ScreencopyView (no KWin protocol).
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Wayland
import Quickshell.Services.Mpris
import org.kde.ksvg as KSvg
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PC3
import qs.modules.plasma.theme
PopupWindow {
    id:popup
    required property var taskItem
    required property var group
    required property var tasksModel
    property string edge:"bottom"
    property bool opened:false
    property var mprisPlayers: Mpris.players?.values ?? []
    readonly property var mediaPlayer: {
        const raw = String(group?.appId ?? "").toLowerCase().replace(/\.desktop$/, "");
        if (!raw) return null;
        const list = mprisPlayers ?? [];
        for (let i = 0; i < list.length; ++i) {
            const p = list[i];
            if (!p) continue;
            const de = String(p.desktopEntry ?? "").toLowerCase().replace(/\.desktop$/, "");
            const id = String(p.identity ?? "").toLowerCase();
            const bus = String(p.dbusName ?? "").toLowerCase();
            if ((de && (de === raw || de.endsWith("." + raw) || raw.endsWith("." + de)))
                || (bus && bus.indexOf("." + raw) !== -1)
                || (id && (id === raw || id.indexOf(raw) !== -1))) {
                return p;
            }
        }
        return null;
    }
    visible:opened && (group?.toplevels.length??0)>0
    color:"transparent"
    anchor {
        item:popup.taskItem
        edges:popup.edge==="bottom"?Edges.Top:popup.edge==="top"?Edges.Bottom:popup.edge==="left"?Edges.Right:Edges.Left
        gravity:popup.edge==="bottom"?Edges.Top:popup.edge==="top"?Edges.Bottom:popup.edge==="left"?Edges.Right:Edges.Left
    }
    implicitWidth:row.implicitWidth+16; implicitHeight:row.implicitHeight+16
    Connections {
        target:popup.taskItem
        function onContainsMouseChanged() {
            if(popup.taskItem.containsMouse) { closeTimer.stop(); openTimer.restart(); }
            else { openTimer.stop(); closeTimer.restart(); }
        }
    }
    Timer { id:openTimer; interval:400; onTriggered:popup.opened=(popup.group?.toplevels.length??0)>0 }
    Timer { id:closeTimer; interval:400; onTriggered:if(!hover.hovered) popup.opened=false }
    HoverHandler { id:hover; onHoveredChanged:if(!hovered) closeTimer.restart() }
    // ToolTipDialog: «widgets/tooltip», translucent with KWin's blur (panel popups are blurred)
    BlurPath { id:tooltipPath; path:"widgets/tooltip"; withoutBlur:"dialogs/background" }
    KSvg.FrameSvgItem { anchors.fill:parent; imagePath:tooltipPath.resolved }
    RowLayout {
        id:row; anchors.centerIn:parent; spacing:8
        Repeater {
            model:popup.group?.toplevels??[]
            delegate:MouseArea {
                id:card
                required property var modelData
                readonly property bool isMinimized: typeof popup.tasksModel?.minimized === "function"
                    ? !!popup.tasksModel.minimized(card.modelData) : false
                readonly property bool canCapture: popup.visible && !card.isMinimized && (card.modelData != null)
                readonly property string appIcon: Quickshell.iconPath(
                    popup.tasksModel?.entry(popup.group?.appId??"")?.icon||"application-x-executable")
                implicitWidth:190; implicitHeight:popup.mediaPlayer ? 172 : 140
                onClicked: { popup.tasksModel.activate(modelData); popup.opened=false; }
                ColumnLayout {
                    anchors.fill:parent; spacing:4
                    RowLayout {
                        Layout.fillWidth:true; spacing:4
                        Kirigami.Icon {
                            Layout.preferredWidth:16; Layout.preferredHeight:16
                            source:card.appIcon
                        }
                        PC3.Label { Layout.fillWidth:true; text:card.modelData.title; elide:Text.ElideRight }
                        PC3.ToolButton {
                            implicitWidth:20; implicitHeight:20
                            icon.name:"window-close"
                            onClicked:if(typeof card.modelData.close==="function"){card.modelData.close();popup.opened=false;}
                        }
                    }
                    Item {
                        Layout.fillWidth:true; Layout.fillHeight:true
                        // Guarded by popup.visible + !isMinimized + Hyprland bwmScreenshareMonitorGuard.
                        ScreencopyView {
                            objectName:"taskThumb"
                            anchors.fill:parent
                            captureSource:card.canCapture ? card.modelData : null
                            live:card.canCapture
                            visible:card.canCapture
                        }
                        Kirigami.Icon {
                            anchors.centerIn:parent
                            width:48; height:48
                            visible:!card.canCapture
                            source:card.appIcon
                        }
                    }
                    RowLayout {
                        objectName:"mediaRow"
                        visible:popup.mediaPlayer !== null
                        Layout.fillWidth:true; spacing:2
                        PC3.Label {
                            objectName:"mediaTrackLabel"
                            Layout.fillWidth:true
                            text:popup.mediaPlayer ? (popup.mediaPlayer.trackTitle || popup.mediaPlayer.identity || "") : ""
                            elide:Text.ElideRight
                            font.pointSize:Math.max(8, Math.round((Kirigami.Theme.smallFont?.pointSize ?? 8)))
                            opacity:0.85
                        }
                        PC3.ToolButton {
                            objectName:"mediaPrev"
                            implicitWidth:22; implicitHeight:22
                            icon.name:"media-skip-backward"
                            enabled:!!(popup.mediaPlayer?.canGoPrevious ?? true)
                            onClicked:if(typeof popup.mediaPlayer?.previous==="function") popup.mediaPlayer.previous()
                        }
                        PC3.ToolButton {
                            objectName:"mediaToggle"
                            implicitWidth:22; implicitHeight:22
                            icon.name:(popup.mediaPlayer?.isPlaying ?? false) ? "media-playback-pause" : "media-playback-start"
                            enabled:!!((popup.mediaPlayer?.canPlay ?? true) || (popup.mediaPlayer?.canPause ?? true))
                            onClicked:if(typeof popup.mediaPlayer?.togglePlaying==="function") popup.mediaPlayer.togglePlaying()
                        }
                        PC3.ToolButton {
                            objectName:"mediaNext"
                            implicitWidth:22; implicitHeight:22
                            icon.name:"media-skip-forward"
                            enabled:!!(popup.mediaPlayer?.canGoNext ?? true)
                            onClicked:if(typeof popup.mediaPlayer?.next==="function") popup.mediaPlayer.next()
                        }
                    }
                }
            }
        }
    }
}
