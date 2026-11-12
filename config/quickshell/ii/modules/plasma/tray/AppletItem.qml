/* SPDX-FileCopyrightText: 2015 Marco Martin <mart@kde.org>
   SPDX-FileCopyrightText: 2022 ivan tkachenko <me@ratijas.tk>
   SPDX-License-Identifier: LGPL-2.0-or-later */
// BWM: PlasmoidItem's compact icon uses BWM's applet state instead of an attached Plasmoid.
import QtQuick
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
AbstractItem {
    id:taskIcon
    required property var applet
    itemId:"applet:"+applet.id
    text:applet.title;mainText:applet.title;subText:"";textFormat:Text.PlainText
    status:PlasmaCore.Types.ActiveStatus
    active:!tray.expanded || tray.activeApplet!==applet.id
    effectivePressed:tray.expanded&&tray.activeApplet===applet.id
    Kirigami.Icon {
        parent:taskIcon.iconContainer;anchors.fill:parent
        source:taskIcon.applet.icon;active:taskIcon.containsMouse
    }
    onActivated:tray.openApplet(applet.id)
    onClicked:mouse=>{if(mouse.button===Qt.LeftButton)activated(null)}
}
