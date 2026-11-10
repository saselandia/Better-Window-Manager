// BWM: settings for the supported containment widgets; external plasmoid hosting is deferred.
import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.modules.common
import org.kde.ksvg as KSvg
import org.kde.plasma.components as PC3
PopupWindow {
    id:root
    property string edge:"bottom"
    readonly property var config:Config.options.bar.plasma
    color:"transparent"; implicitWidth:380; implicitHeight:690
    anchor.edges:edge==="bottom"?Edges.Top:edge==="top"?Edges.Bottom:edge==="left"?Edges.Right:Edges.Left
    anchor.gravity:anchor.edges
    KSvg.FrameSvgItem { anchors.fill:parent; imagePath:"dialogs/background" }
    ColumnLayout {
        anchors.fill:parent; anchors.margins:16; spacing:8
        PC3.Label { text:"Configurar panel"; font.bold:true }
        PC3.ComboBox { Layout.fillWidth:true; model:[({label:"Abajo",value:"bottom"}),({label:"Arriba",value:"top"}),({label:"Izquierda",value:"left"}),({label:"Derecha",value:"right"})]; textRole:"label"; valueRole:"value"; currentIndex:indexOfValue(root.config.edge||root.edge); onActivated:root.config.edge=currentValue }
        PC3.ComboBox { Layout.fillWidth:true; model:[({label:"Siempre visible",value:"always"}),({label:"Ocultar automáticamente",value:"autoHide"}),({label:"Esquivar ventanas",value:"dodge"}),({label:"Ventanas por debajo",value:"windowsGoBelow"})]; textRole:"label"; valueRole:"value"; currentIndex:indexOfValue(root.config.visibility); onActivated:root.config.visibility=currentValue }
        PC3.ComboBox { Layout.fillWidth:true; model:[({label:"Adaptable",value:"adaptive"}),({label:"Traslúcido",value:"translucent"}),({label:"Opaco",value:"opaque"})]; textRole:"label"; valueRole:"value"; currentIndex:indexOfValue(root.config.style==="floating"?"adaptive":root.config.style); onActivated:root.config.style=currentValue }
        PC3.ComboBox { Layout.fillWidth:true; model:[({label:"Inicio",value:"start"}),({label:"Centro",value:"center"}),({label:"Final",value:"end"})]; textRole:"label"; valueRole:"value"; currentIndex:indexOfValue(root.config.alignment); onActivated:root.config.alignment=currentValue }
        PC3.CheckBox { text:"Flotante"; checked:root.config.floating; onToggled:root.config.floating=checked }
        RowLayout {
            PC3.Label { text:"Grosor" }
            PC3.Slider { Layout.fillWidth:true; from:24; to:96; stepSize:2; value:root.config.thickness||44; onMoved:root.config.thickness=value }
        }
        RowLayout {
            PC3.Label { text:"Longitud" }
            PC3.Slider { Layout.fillWidth:true; from:.25; to:1; stepSize:.05; value:root.config.length; onMoved:root.config.length=value }
        }
        PC3.Label { text:"Widgets incluidos"; font.bold:true }
        Flow {
            Layout.fillWidth:true; Layout.preferredHeight:72; spacing:4
            Repeater {
                model:["kickoff","pager","tasks","tray","clock","desktop"]
                PC3.CheckBox {
                    required property string modelData
                    text:modelData; checked:(root.config.widgets??[]).includes(modelData)
                    onToggled: {
                        const current=root.config.widgets??[];
                        root.config.widgets=checked?current.concat([modelData]):current.filter(x=>x!==modelData);
                    }
                }
            }
        }
        Repeater {
            model:root.config.widgets
            RowLayout {
                required property string modelData
                required property int index
                PC3.Label { Layout.fillWidth:true; text:parent.modelData }
                PC3.ToolButton {
                    icon.name:"go-up"; enabled:parent.index>0
                    onClicked: {
                        const values=root.config.widgets.slice();
                        const i=parent.index;
                        [values[i-1],values[i]]=[values[i],values[i-1]];
                        root.config.widgets=values;
                    }
                }
                PC3.ToolButton {
                    icon.name:"go-down"; enabled:parent.index<root.config.widgets.length-1
                    onClicked: {
                        const values=root.config.widgets.slice();
                        const i=parent.index;
                        [values[i+1],values[i]]=[values[i],values[i+1]];
                        root.config.widgets=values;
                    }
                }
            }
        }
        PC3.Button { text:"Terminar"; Layout.alignment:Qt.AlignRight; onClicked: { PanelState.setEditing(root.anchor.item.QsWindow.window?.screen?.name??"",false); root.visible=false; } }
    }
}
