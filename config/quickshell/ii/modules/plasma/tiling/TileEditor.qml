// SPDX-License-Identifier: GPL-2.0-or-later
// BWM F10: reduced editor over the original KWin tile JSON, never a private layout format.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore

Scope {
    id: root
    property var data: null
    property var selected: []
    property string error: ""
    property bool opened: false
    readonly property string script: Quickshell.env("HOME")+"/.config/hypr/skins/plasma/scripts/kwin-tiles.py"
    function load(monitor,output): void {
        if (worker.running) return;
        const args=["python3",script,"inspect"];
        if (monitor) args.push("--monitor","desc:"+monitor);
        if (output) args.push("--output",output);
        worker.command=args; worker.running=true;
    }
    function edit(operation): void {
        if (!root.data || worker.running) return;
        const payload=Object.assign({},root.data,{selected:root.selected,ratio:ratio.value/100});
        worker.command=["python3",script,"edit",operation,JSON.stringify(payload)];
        worker.running=true;
    }
    IpcHandler {
        target: "plasmaTiles"
        function open(): void { root.opened=true; root.load("",""); }
        function close(): void { root.opened=false; }
        function inspect(): string {return JSON.stringify({opened:root.opened,data:root.data,error:root.error});}
    }
    Process {
        id: worker
        property string result: ""
        stdout: StdioCollector {onStreamFinished:worker.result=text}
        stderr: StdioCollector {onStreamFinished:if(text.trim())root.error=text.trim()}
        onExited: (code,status)=> {
            if(code===0) {
                root.error="";
                if(worker.result.trim()) {
                    try {root.data=JSON.parse(worker.result);root.selected=[]} catch(e){root.error=String(e)}
                } else if(worker.command[2]==="edit" && worker.command[3]==="save") root.opened=false;
            }
            worker.result="";
        }
    }
    FloatingWindow {
        id: win
        visible: root.opened
        title: qsTr("Editor de mosaico — Breeze")
        implicitWidth: 960
        implicitHeight: 650
        color: Kirigami.Theme.backgroundColor
        // Esc cancela sin guardar, como el editor de mosaico de KWin
        Shortcut { sequences: [StandardKey.Cancel]; enabled: win.visible; onActivated: root.opened = false }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing
            PC3.Label {text:qsTr("Mosaico personalizado");font.bold:true;font.pointSize:18}
            PC3.Label {text:qsTr("Selecciona una zona para dividirla. Mantén Mayús al arrastrar una ventana para encajarla.");wrapMode:Text.Wrap;Layout.fillWidth:true}
            RowLayout {
                PC3.ComboBox {
                    model:root.data?.monitors ?? []
                    currentIndex:root.data?.monitors?.indexOf(root.data.description) ?? 0
                    onActivated:if(root.data)root.load(currentText,"")
                }
                PC3.ComboBox {
                    model:(root.data?.outputs ?? []).map((id,index)=>qsTr("Distribución %1").arg(index+1))
                    currentIndex:root.data?.outputs?.indexOf(root.data.output) ?? 0
                    onActivated:if(root.data)root.load(root.data.description,root.data.outputs[currentIndex])
                    Layout.preferredWidth:170
                }
                PC3.Label {text:qsTr("Separación")}
                PC3.SpinBox {from:0;to:100;value:root.data?.padding ?? 4;onValueModified:if(root.data)root.data=Object.assign({},root.data,{padding:value})}
            }
            Item {
                id: canvas
                Layout.fillWidth:true
                Layout.fillHeight:true
                Repeater {
                    model:root.data?.leaves ?? []
                    Rectangle {
                        id: tile
                        required property var modelData
                        x:modelData.x*canvas.width+2
                        y:modelData.y*canvas.height+2
                        width:modelData.width*canvas.width-4
                        height:modelData.height*canvas.height-4
                        color:Kirigami.Theme.alternateBackgroundColor
                        border.color:JSON.stringify(root.selected)===JSON.stringify(modelData.path)?Kirigami.Theme.highlightColor:Kirigami.Theme.disabledTextColor
                        border.width:2
                        radius:Kirigami.Units.cornerRadius
                        PC3.Label {anchors.centerIn:parent;text:Math.round(tile.modelData.width*100)+" % × "+Math.round(tile.modelData.height*100)+" %"}
                        MouseArea {anchors.fill:parent;onClicked:root.selected=tile.modelData.path}
                    }
                }
            }
            RowLayout {
                PC3.Button {text:qsTr("Dividir horizontalmente");enabled:!!root.data&&!worker.running;onClicked:root.edit("split-horizontal")}
                PC3.Button {text:qsTr("Dividir verticalmente");enabled:!!root.data&&!worker.running;onClicked:root.edit("split-vertical")}
                PC3.Button {text:qsTr("Unir división");enabled:root.selected.length>0&&!worker.running;onClicked:root.edit("join")}
                PC3.SpinBox {id:ratio;from:10;to:90;stepSize:5;value:50}
                PC3.Button {text:qsTr("Repartir (%)");enabled:root.selected.length>0&&!worker.running;onClicked:root.edit("ratio")}
                Item {Layout.fillWidth:true}
                PC3.Button {text:qsTr("Cancelar");onClicked:root.opened=false}
                PC3.Button {text:qsTr("Aplicar");enabled:!!root.data&&!worker.running;onClicked:root.edit("save")}
            }
            PC3.Label {visible:root.error.length>0;text:root.error;color:Kirigami.Theme.negativeTextColor;wrapMode:Text.Wrap;Layout.fillWidth:true}
        }
    }
}
