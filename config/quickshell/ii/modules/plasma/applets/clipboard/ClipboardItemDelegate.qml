/* SPDX-FileCopyrightText: 2014 Martin Gräßlin <mgraesslin@kde.org>
   SPDX-FileCopyrightText: 2014 Sebastian Kügler <sebas@kde.org>
   SPDX-License-Identifier: GPL-2.0-or-later */
// BWM: Klipper delegate base reduced to text/copy/delete, with cliphist IDs and no Klipper service.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3
PC3.ItemDelegate {
    id:row
    required property var model
    property alias mainItem:label.contentItem
    property alias dragHandler:dragHandler
    signal selected()
    signal remove()
    implicitHeight:Math.max(44,label.implicitHeight+12)
    onClicked:selected()
    Keys.onDeletePressed:remove()
    contentItem:RowLayout {
        PC3.Control { id:label; Layout.fillWidth:true; padding:0 }
        PC3.ToolButton { icon.name:"edit-delete"; onClicked:row.remove() }
    }
    DragHandler { id:dragHandler; enabled:false }
}
