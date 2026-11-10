import QtQuick
import QtQuick.Controls

Button {
    id: control
    required property var style
    property bool primary: false
    property bool chosen: false
    font.family: style.font
    font.pixelSize: 13
    leftPadding: 16
    rightPadding: 16
    topPadding: 10
    bottomPadding: 10
    hoverEnabled: true
    opacity: enabled ? 1 : 0.45
    contentItem: Text {
        text: control.text
        font: control.font
        color: control.primary ? control.style.onAccent : control.style.foreground
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: control.style.buttonRadius
        color: control.primary ? control.style.accent :
               control.chosen || control.hovered || control.activeFocus ? control.style.selection : control.style.surface
        border.width: control.activeFocus || control.chosen ? 2 : 1
        border.color: control.activeFocus || control.chosen ? control.style.accent : control.style.border
    }
}
