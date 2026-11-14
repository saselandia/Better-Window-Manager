// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import org.kde.kirigami as Kirigami
MouseArea {
    id: compact
    readonly property var plasmoidItem: parent && parent.plasmoidItem ? parent.plasmoidItem : parent
    implicitWidth: 32
    implicitHeight: 32
    onClicked: if (plasmoidItem) plasmoidItem.expanded = !plasmoidItem.expanded
    Kirigami.Icon {
        anchors.fill: parent
        source: compact.plasmoidItem && compact.plasmoidItem.plasmoid ? compact.plasmoidItem.plasmoid.icon : "plasma"
    }
}
