// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import org.bwm.plasma.host 1.0
import org.kde.plasma.core as PlasmaCore
Item {
    id: root
    property Item plasmoidItem
    property Item compactRepresentation
    property Item fullRepresentation
    readonly property alias popup: popup
    objectName: "bwmCompactExpander"
    onCompactRepresentationChanged: {
        if (compactRepresentation) {
            compactRepresentation.parent = root;
            compactRepresentation.anchors.fill = root;
        }
    }
    property PopupAnchor anchorAdapter: PopupAnchor { popup: popup; visualParent: root.plasmoidItem }
    PlasmaCore.AppletPopup {
        id: popup
        objectName: "bwmAppletPopup"
        appletInterface: root.plasmoidItem
        visualParent: root.plasmoidItem
        popupDirection: Qt.TopEdge
        mainItem: root.fullRepresentation
        hideOnWindowDeactivate: true
        visible: root.plasmoidItem.expanded && root.fullRepresentation !== null
        onVisibleChanged: if (!visible && root.plasmoidItem.expanded) root.plasmoidItem.expanded = false
    }
}
