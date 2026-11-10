// BWM: containment layout on Quickshell; the tasks/clock compact representations are ported.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Hyprland
import qs
import qs.services
import qs.modules.common
import qs.modules.ii.bar as SharedBar
import qs.modules.ii.plasmaCommon
import org.kde.plasma.components as PC3
Item {
    id:root
    required property var panelWindow
    property string edge:"bottom"
    property bool vertical:edge==="left"||edge==="right"
    readonly property var config:Config.options.bar.plasma
    readonly property var widgets:config.widgets ?? ["kickoff","tasks","tray","clock","desktop"]
    TasksModel { id:modelAdapter }
    function menuFor(app,button) {
        GlobalStates.plasmaTaskMenuApp=app;
        PanelState.popup("plasmaTaskMenu",button);
    }
    GridLayout {
        anchors.fill:parent; rowSpacing:2; columnSpacing:2
        rows:root.vertical?-1:1; columns:root.vertical?1:-1
        Repeater {
            model:root.widgets
            delegate:Loader {
                id:widget
                required property string modelData
                Layout.fillWidth:root.vertical||modelData==="tasks"
                Layout.fillHeight:!root.vertical||modelData==="tasks"
                Layout.minimumWidth:root.vertical?0:(modelData==="tasks"?44:0)
                Layout.minimumHeight:root.vertical&&modelData==="tasks"?44:0
                Layout.preferredWidth:root.vertical?-1:implicitWidth
                Layout.preferredHeight:root.vertical?implicitHeight:-1
                sourceComponent:({
                    kickoff:kickoffComponent,pager:pagerComponent,tasks:tasksComponent,
                    tray:trayComponent,clock:clockComponent,desktop:desktopComponent
                })[modelData] ?? null
            }
        }
        PC3.ToolButton {
            visible:root.panelWindow.editing
            Layout.preferredWidth:32; Layout.preferredHeight:32
            icon.name:"configure"; onClicked:editor.visible=!editor.visible
            PanelEditor { id:editor; anchor.item:parent; edge:root.edge }
        }
    }
    Component {
        id:kickoffComponent
        PC3.ToolButton {
            implicitWidth:40; implicitHeight:40
            icon.name:"start-here-kde"
            onClicked: {
                Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/app-launcher.sh"]);
            }
        }
    }
    Component {
        id:pagerComponent
        GridLayout {
            columns:root.vertical?2:Config.options.bar.workspaces.shown
            Repeater {
                model:Config.options.bar.workspaces.shown
                PC3.ToolButton {
                    required property int index
                    implicitWidth:22; implicitHeight:22
                    text:String(index+1)
                    checked:root.panelWindow.monitor?.activeWorkspace?.id===index+1; checkable:true
                    onClicked:Hyprland.dispatch("hl.dsp.focus({workspace = "+String(index+1)+"})")
                }
            }
        }
    }
    Component {
        id:tasksComponent
        ListView {
            id:list
            implicitWidth:root.vertical?40:Math.max(44,contentWidth)
            implicitHeight:root.vertical?Math.max(44,contentHeight):40
            orientation:root.vertical?ListView.Vertical:ListView.Horizontal
            spacing:2; clip:true; boundsBehavior:Flickable.StopAtBounds
            model:ScriptModel { objectProp:"appId"; values:modelAdapter.groups }
            delegate:Task {
                required property var modelData
                group:modelData; tasksModel:modelAdapter; edge:root.edge
                width:root.vertical?list.width:Math.min(52,list.height+4)
                height:root.vertical?Math.min(52,list.width+4):list.height
                onContextRequested:button=>root.menuFor(modelData.appId,button)
            }
        }
    }
    Component {
        id:trayComponent
        GridLayout {
            rows:root.vertical?-1:1; columns:root.vertical?1:-1
            SharedBar.SysTray {
                vertical:root.vertical; itemSize:22
                Layout.preferredWidth:root.vertical?32:implicitWidth
                Layout.preferredHeight:root.vertical?implicitHeight:32
            }
            PC3.ToolButton { icon.name:"audio-volume-high"; implicitWidth:30; implicitHeight:30; onClicked:PanelState.popup("plasmaAudio",this) }
            PC3.ToolButton { icon.name:"network-wireless"; implicitWidth:30; implicitHeight:30; onClicked:PanelState.popup("plasmaNetwork",this) }
            PC3.ToolButton { icon.name:"bluetooth"; implicitWidth:30; implicitHeight:30; visible:BluetoothStatus.available; onClicked:PanelState.popup("plasmaBluetooth",this) }
            PC3.ToolButton { icon.name:"notifications"; implicitWidth:30; implicitHeight:30; onClicked:PanelState.popup("plasmaNotifications",this) }
        }
    }
    Component {
        id:clockComponent
        DigitalClock {
            vertical:root.vertical
            showDate:root.config.showDate
            showSeconds:root.config.showSeconds
            onClicked:PanelState.popup("plasmaCalendar",this)
        }
    }
    Component {
        id:desktopComponent
        PC3.ToolButton {
            implicitWidth:root.vertical?32:20; implicitHeight:root.vertical?20:32
            icon.name:"user-desktop"; onClicked:PlasmaPanelState.toggleShowDesktop()
        }
    }
}
