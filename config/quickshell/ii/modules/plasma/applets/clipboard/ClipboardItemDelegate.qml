/* SPDX-FileCopyrightText: 2014 Martin Gräßlin <mgraesslin@kde.org>
   SPDX-FileCopyrightText: 2014 Sebastian Kügler <sebas@kde.org>
   SPDX-License-Identifier: GPL-2.0-or-later */
// BWM: Klipper delegate base reduced to label + DelegateToolButtons, with cliphist IDs and no
// Klipper service. As in Klipper, the tool buttons appear on the row under the pointer or with
// keyboard focus; `type` follows HistoryItemType (2 = text, 4 = image).
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami
PC3.ItemDelegate {
    id:row
    required property var model
    property int type:2
    property alias mainItem:label.contentItem
    property alias dragHandler:dragHandler
    readonly property bool shouldUseOverflowButton:false
    signal selected()
    signal remove()
    signal edit()
    signal barcode()
    implicitHeight:Math.max(44,label.implicitHeight+12)
    onClicked:selected()
    Keys.onDeletePressed:remove()
    contentItem:RowLayout {
        PC3.Control { id:label; Layout.fillWidth:true; padding:0 }
        DelegateToolButtons {
            objectName:"plasma-clipboard-tools"
            visible:row.hovered||row.activeFocus||hovered
            menuItem:row
            shouldUseOverflowButton:row.shouldUseOverflowButton
        }
    }
    DragHandler { id:dragHandler; enabled:false }
}
