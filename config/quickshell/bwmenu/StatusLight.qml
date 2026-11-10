import QtQuick
import QtQuick.Controls

Item {
    id: root
    property string state: "unknown"
    property string description: "Comprobando"
    readonly property color tint: state === "ok" ? "#169447" : state === "newer" ? "#ed8b13" : state === "error" ? "#d83232" : "#9299a2"
    implicitWidth: 20
    implicitHeight: 20
    Accessible.name: description
    Rectangle { anchors.centerIn: parent; width: 18; height: 18; radius: 9; color: root.tint; opacity: 0.14 }
    Rectangle { anchors.centerIn: parent; width: 9; height: 9; radius: 5; color: root.tint }
    MouseArea { id: hover; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
    ToolTip.visible: hover.containsMouse
    ToolTip.text: description
    ToolTip.delay: 250
}
