/* SPDX-FileCopyrightText: 2018-2019 Kai Uwe Broulik <kde@privat.broulik.de>
   SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL */
// BWM: FullRepresentation's DND header/history layout; data comes from the BWM server.
import QtQuick
import QtQuick.Layouts
import qs.services
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import "notifications"
AppletHost {
    id:root
    translationDomain:"plasma_applet_org.kde.plasma.notifications"
    property var backend:Notifications
    onExpandedChanged:if(expanded&&!readOnly) { backend.markAllRead();backend.timeoutAll(); }
    fullRepresentation: PlasmaExtras.Representation {
        header:PlasmaExtras.PlasmoidHeading {
            RowLayout {
                anchors.fill:parent
                PC3.Switch { text:root.i18n("Do not disturb"); checked:root.backend.silent; enabled:!root.readOnly; onToggled:root.backend.silent=checked }
                Item { Layout.fillWidth:true }
                PC3.ToolButton { icon.name:"edit-clear-history"; text:root.i18n("Clear All"); enabled:!root.readOnly&&root.backend.list.length>0; onClicked:root.backend.discardAllNotifications() }
            }
        }
        PC3.ScrollView {
            anchors.fill:parent
            ListView {
                id:history
                model:root.backend.list.slice().reverse();clip:true; spacing:4
                delegate:NotificationCard { required property var modelData; width:history.width; notification:modelData; backend:root.backend; readOnly:root.readOnly }
                PlasmaExtras.PlaceholderMessage { anchors.centerIn:parent; visible:history.count===0; text:root.i18n("No unread notifications") }
            }
        }
    }
}
