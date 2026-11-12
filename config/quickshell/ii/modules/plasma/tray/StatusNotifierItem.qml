/* SPDX-FileCopyrightText: 2016 Marco Martin <mart@kde.org>
   SPDX-License-Identifier: LGPL-2.0-or-later */
// BWM: original SNI icon/events mapped to Quickshell instead of Plasma's data engine.
import QtQuick
import Quickshell
import Quickshell.Services.SystemTray
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
AbstractItem {
    id:taskIcon
    required property var item
    itemId:item.id
    text:item.title||item.tooltipTitle||item.id
    mainText:item.tooltipTitle; subText:item.tooltipDescription
    textFormat:Text.AutoText
    active:true
    status:item.status===Status.NeedsAttention?PlasmaCore.Types.NeedsAttentionStatus:PlasmaCore.Types.ActiveStatus
    // BWM: Plasma passes a QIcon, which Kirigami.Icon keeps square; Quickshell gives an image URL, which
    // Kirigami.Icon stretches to the container (itemSize x cell height). Keep it square and centred.
    Kirigami.Icon {
        parent:taskIcon.iconContainer;anchors.centerIn:parent
        width:Math.min(parent.width,parent.height);height:width
        source:taskIcon.item.icon;active:taskIcon.containsMouse
    }
    onActivated:pos=>{ if(item.onlyMenu)tray.openMenu(item,taskIcon);else item.activate(); }
    onContextMenu:mouse=>tray.openMenu(item,taskIcon)
    onClicked:mouse=>{
        if(mouse.button===Qt.RightButton)tray.openMenu(item,taskIcon);
        else if(mouse.button===Qt.MiddleButton)item.secondaryActivate();
        else activated(Qt.point(mouse.x,mouse.y));
    }
    onWheel:wheel=>{if(wheel.angleDelta.y)item.scroll(wheel.angleDelta.y,false);if(wheel.angleDelta.x)item.scroll(wheel.angleDelta.x,true);}
}
