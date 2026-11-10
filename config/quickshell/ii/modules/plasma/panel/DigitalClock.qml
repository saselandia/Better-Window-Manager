/*
    SPDX-FileCopyrightText: 2013 Heena Mahour <heena393@gmail.com>
    SPDX-FileCopyrightText: 2013 Sebastian Kügler <sebas@kde.org>
    SPDX-FileCopyrightText: 2013 Martin Klapetek <mklapetek@kde.org>
    SPDX-FileCopyrightText: 2014 David Edmundson <davidedmundson@kde.org>
    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM: compact local-time representation adapted from plasma-workspace v6.7.5
// applets/digital-clock/DigitalClock.qml. Configuration/expanded provided by the panel.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami
import org.kde.plasma.clock
import qs.modules.common
MouseArea {
    id: main
    property bool vertical:false
    property bool showDate:true
    property string dateFormat:"shortDate"
    property string customDateFormat:"ddd d"
    property bool showSeconds:false
    property string timeFormat:Config.options?.time?.format || Qt.locale().timeFormat(Locale.ShortFormat)
    readonly property bool oneLineMode: !vertical && height<=2*Kirigami.Theme.smallFont.pixelSize && showDate
    readonly property var dateFormatter: {
        if(dateFormat==="custom") return d=>Qt.locale().toString(d,customDateFormat);
        else if(dateFormat==="isoDate") return d=>Qt.formatDate(d,Qt.ISODate);
        else if(dateFormat==="longDate") return d=>Qt.formatDate(d,Qt.locale(),Locale.LongFormat);
        else return d=>Qt.formatDate(d,Qt.locale(),Locale.ShortFormat);
    }
    implicitWidth: vertical ? 40 : Math.max(72,layout.implicitWidth+12)
    implicitHeight: 36
    clip:true
    hoverEnabled:true
    Accessible.role:Accessible.Button
    Clock { id:clock; timeZone:"Local"; trackSeconds:main.showSeconds }
    GridLayout {
        id:layout; anchors.centerIn:parent
        columns:main.oneLineMode?2:1; rowSpacing:0; columnSpacing:4
        PC3.Label {
            Layout.alignment:Qt.AlignHCenter
            text: Qt.formatTime(clock.dateTime,main.showSeconds ? "hh:mm:ss" : main.timeFormat)
            font.family:Kirigami.Theme.defaultFont.family; font.pointSize:Kirigami.Theme.defaultFont.pointSize
            font.bold:true
            fontSizeMode:Text.Fit
            Layout.minimumWidth:0
            Layout.preferredWidth:main.vertical?main.width:-1
            Layout.maximumWidth:main.vertical?main.width:200
            minimumPixelSize:8
        }
        PC3.Label {
            visible:main.showDate; Layout.alignment:Qt.AlignHCenter
            text:main.vertical ? Qt.formatDate(clock.dateTime,"d MMM") : main.dateFormatter(clock.dateTime)
            font:Kirigami.Theme.smallFont
            fontSizeMode:Text.Fit; minimumPixelSize:8
            Layout.minimumWidth:0
            Layout.preferredWidth:main.vertical?main.width:-1
            Layout.maximumWidth:main.vertical?main.width:180
        }
    }
}
