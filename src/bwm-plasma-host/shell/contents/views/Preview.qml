// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import QtQuick.Layouts
Rectangle {
    id: root
    color: Kirigami.Theme.backgroundColor
    required property Item appletItem
    required property var applet
    required property var configurationSession
    required property var catalog
    ColumnLayout {
        anchors.fill: parent
        RowLayout {
            QQC2.Button { objectName: "configureButton"; text: qsTr("Configure…"); onClicked: root.configurationSession.show() }
            QQC2.Button { objectName: "getNewButton"; text: qsTr("Get New Widgets…"); onClicked: root.catalog.getNewWidgets() }
            QQC2.Button {
                id: actionsButton
                objectName: "actionsButton"
                text: qsTr("Actions")
                onClicked: actionsMenu.popup()
                QQC2.Menu {
                    id: actionsMenu
                    popupType: QQC2.Popup.Item
                    onAboutToShow: root.applet.contextualActionsAboutToShow()
                    Instantiator {
                        model: root.applet.contextualActions
                        delegate: QQC2.MenuItem {
                            required property var modelData
                            objectName: modelData.objectName
                            text: modelData.text
                            enabled: modelData.enabled
                            visible: modelData.visible
                            checkable: modelData.checkable
                            checked: modelData.checked
                            onTriggered: modelData.trigger()
                        }
                        onObjectAdded: (index, object) => actionsMenu.insertItem(index, object)
                        onObjectRemoved: (index, object) => actionsMenu.removeItem(object)
                    }
                }
            }
            QQC2.Label { text: root.catalog.entries.filter(entry => entry.catalogVisible).length + qsTr(" available widgets") }
        }
        QQC2.Label { Layout.fillWidth: true; text: root.catalog.error; visible: text.length > 0; wrapMode: Text.Wrap }
        Item {
            id: stage
            Layout.fillWidth: true
            Layout.fillHeight: true
            Component.onCompleted: {
                root.appletItem.parent = stage;
                root.appletItem.anchors.centerIn = stage;
            }
        }
    }
}
