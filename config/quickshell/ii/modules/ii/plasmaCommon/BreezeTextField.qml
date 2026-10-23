import QtQuick
import QtQuick.Layouts

// Breeze line edit with placeholder and optional leading icon
Rectangle {
    id: tf
    property alias text: input.text
    property alias echoMode: input.echoMode
    property alias input: input
    property string placeholder: ""
    property url iconSource: ""
    signal accepted()
    signal escapePressed()
    implicitHeight: 28
    radius: 4
    color: Breeze.inputBg
    border.width: input.activeFocus ? 1.5 : 1
    border.color: input.activeFocus ? Breeze.accent : Breeze.buttonBorder

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        spacing: 6

        Image {
            visible: tf.iconSource.toString().length > 0
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            sourceSize: Qt.size(16, 16)
            source: tf.iconSource
        }
        TextInput {
            id: input
            Layout.fillWidth: true
            verticalAlignment: TextInput.AlignVCenter
            color: Breeze.text
            selectionColor: Breeze.accent
            font.family: Breeze.fontFamily
            font.pixelSize: 12
            clip: true
            onAccepted: tf.accepted()
            Keys.onEscapePressed: tf.escapePressed()

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: tf.placeholder
                color: Breeze.textMuted
                font: input.font
                visible: !input.text && !input.inputMethodComposing
            }
        }
    }
}
