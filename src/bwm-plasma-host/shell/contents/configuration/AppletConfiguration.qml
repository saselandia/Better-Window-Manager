// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
Rectangle {
    id: root
    color: Kirigami.Theme.backgroundColor
    implicitWidth: 800
    implicitHeight: 600
    property int currentPage: 0
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        QQC2.Label {
            Layout.fillWidth: true
            text: bwmConfigSession.error
            visible: text.length > 0
            wrapMode: Text.Wrap
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            QQC2.ScrollView {
                Layout.preferredWidth: 180
                Layout.fillHeight: true
                Column {
                    width: parent.width
                    Repeater {
                        model: bwmConfigSession.pages
                        delegate: QQC2.Button {
                            required property var modelData
                            required property int index
                            width: 170
                            objectName: "categoryButton_" + index
                            text: modelData.name
                            checkable: true
                            checked: root.currentPage === index
                            onClicked: root.currentPage = index
                        }
                    }
                }
            }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Repeater {
                    model: bwmConfigSession.pages
                    delegate: Item {
                        id: holder
                        required property var modelData
                        required property int index
                        anchors.fill: parent
                        visible: root.currentPage === index
                        Component.onCompleted: {
                            modelData.item.parent = holder;
                            modelData.item.anchors.fill = holder;
                        }
                    }
                }
            }
        }
        RowLayout {
            QQC2.Button { objectName: "defaultsButton"; enabled: bwmConfigSession.pages.length > 0 && bwmConfigSession.error.length === 0; text: qsTr("Defaults"); onClicked: bwmConfigSession.defaults() }
            Item { Layout.fillWidth: true }
            QQC2.Button { objectName: "cancelButton"; text: qsTr("Cancel"); onClicked: bwmConfigSession.cancel() }
            QQC2.Button {
                objectName: "applyButton"
                text: qsTr("Apply")
                enabled: bwmConfigSession.dirty && bwmConfigSession.error.length === 0
                onClicked: bwmConfigSession.apply()
            }
        }
    }
}
