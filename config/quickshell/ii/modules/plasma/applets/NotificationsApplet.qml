/* SPDX-FileCopyrightText: 2018-2019 Kai Uwe Broulik <kde@privat.broulik.de>
   SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL */
// BWM: FullRepresentation's DND header/history layout (with timed DND); data comes from the BWM server.
import QtQuick
import QtQuick.Layouts
import qs.services
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import "notifications"
AppletHost {
    id:root
    translationDomain:"plasma_applet_org.kde.plasma.notifications"
    property var backend:Notifications
    onExpandedChanged:if(expanded&&!readOnly) { backend.markAllRead();backend.timeoutAll(); }
    function minutesUntilTomorrow() {
        const now = new Date();
        const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0, 0);
        return Math.max(1, Math.round((tomorrow.getTime() - now.getTime()) / 60000));
    }
    fullRepresentation: PlasmaExtras.Representation {
        header:PlasmaExtras.PlasmoidHeading {
            ColumnLayout {
                anchors.fill:parent
                spacing:Kirigami.Units.smallSpacing
                RowLayout {
                    Layout.fillWidth:true
                    PC3.Switch {
                        objectName:"plasma-dnd-switch"
                        text:root.i18n("Do not disturb")
                        checked:Boolean(root.backend.silent)
                        enabled:!root.readOnly
                        onToggled:root.backend.silent=checked
                    }
                    Item { Layout.fillWidth:true }
                    PC3.ToolButton { icon.name:"edit-clear-history"; text:root.i18n("Clear All"); enabled:!root.readOnly&&root.backend.list.length>0; onClicked:root.backend.discardAllNotifications() }
                }
                RowLayout {
                    Layout.fillWidth:true
                    visible:Boolean(root.backend.silent) && typeof root.backend.setSilentFor==="function"
                    spacing:Kirigami.Units.smallSpacing
                    PC3.Label {
                        objectName:"plasma-dnd-until-label"
                        Layout.fillWidth:true
                        font:Kirigami.Theme.smallFont
                        opacity:0.8
                        elide:Text.ElideRight
                        text:(root.backend.silentUntil??0)>0
                            ? root.i18n("Until %1", Qt.formatTime(new Date(root.backend.silentUntil), Qt.locale().timeFormat(Locale.ShortFormat)))
                            : root.i18n("Until turned off")
                    }
                    PC3.ComboBox {
                        id:dndDuration
                        objectName:"plasma-dnd-duration"
                        enabled:!root.readOnly
                        Accessible.name:root.i18n("Do not disturb")
                        model:[
                            ({label:root.i18n("Until turned off"),minutes:0}),
                            ({label:root.i18n("For 1 hour"),minutes:60}),
                            ({label:root.i18n("For 4 hours"),minutes:240}),
                            ({label:root.i18n("Until tomorrow"),minutes:-1})
                        ]
                        textRole:"label"
                        onActivated:index=>{
                            const entry = model[index];
                            if (!entry) return;
                            const mins = entry.minutes < 0 ? root.minutesUntilTomorrow() : entry.minutes;
                            root.backend.setSilentFor(mins);
                        }
                    }
                }
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
