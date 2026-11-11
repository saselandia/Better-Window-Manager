// BWM: containment layout on Quickshell; the tasks/clock compact representations are ported.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Hyprland
import qs
import qs.services
import qs.modules.common
import qs.modules.plasma.tray as PlasmaTray
import "." as PanelLocal
import qs.modules.plasma.menus
import org.kde.plasma.components as PC3
Item {
    id:root
    required property var panelWindow
    property string edge:"bottom"
    property bool vertical:edge==="left"||edge==="right"
    readonly property var config:Config.options.bar.plasma
    readonly property var widgets:config.widgets ?? ["kickoff","tasks","tray","clock","desktop"]
    TasksModel { id:modelAdapter }
    // F9: el menú del gestor de tareas de Plasma (modules/plasma/menus/TaskMenu.qml)
    function menuFor(group,button) {
        PlasmaMenus.openFor("task",button,root.edge,{group:group});
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
            // F9: «Añadir o gestionar elementos gráficos…» del menú del panel abre el editor
            Connections {
                target:PlasmaMenus
                function onWidgetsRequested(name) { if(name===root.panelWindow.screen.name) Qt.callLater(()=>editor.visible=true); }
            }
        }
    }
    Component {
        id:kickoffComponent
        PC3.ToolButton {
            implicitWidth:44; implicitHeight:40
            icon.width:32;icon.height:32
            icon.name:Config.options.bar.plasma.kickoff?.icon || "start-here-kde"
            checked:GlobalStates.plasmaKickoffOpen
            // F4: el Kickoff portado (modules/plasma/kickoff) se abre junto a este botón, como el plasmoide
            onClicked: {
                if (GlobalStates.plasmaKickoffOpen) { GlobalStates.plasmaKickoffOpen=false; return; }
                PanelState.anchor(this,"plasmaKickoff");
                GlobalStates.plasmaKickoffOpen=true;
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
                onContextRequested:button=>root.menuFor(modelData,button)
            }
        }
    }
    Component {
        id:trayComponent
        PlasmaTray.SystemTray { vertical:root.vertical }
    }

    Component {
        id:clockComponent
        DigitalClock {
            id:clock
            // BWM: the calendar remains available even if the tray widget is removed.
            QtObject {
                id:calendarHost
                readonly property bool expanded:!root.widgets.includes("tray")&&PlasmaTray.TrayState.expanded&&PlasmaTray.TrayState.applet==="calendar"&&PlasmaTray.TrayState.screenName===root.panelWindow.screen.name
                readonly property string activeApplet:"calendar"
                property bool configuring:false
                readonly property bool configurable:false
                readonly property bool readOnly:false
                readonly property var applets:[]
                readonly property var items:[]
                readonly property var settings:({})
                readonly property var appletProperties:({})
            }
            PlasmaTray.TrayPopup { anchorItem:clock;tray:calendarHost }
            vertical:root.vertical
            showDate:root.config.showDate
            showSeconds:root.config.showSeconds
            onClicked:PlasmaTray.TrayState.toggle("calendar",root.panelWindow.screen.name)
        }
    }
    Component {
        id:desktopComponent
        PC3.ToolButton {
            implicitWidth:root.vertical?32:20; implicitHeight:root.vertical?20:32
            icon.name:"user-desktop";icon.width:20;icon.height:20; onClicked:PanelLocal.DesktopState.toggle()
        }
    }
}
