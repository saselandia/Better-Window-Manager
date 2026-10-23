pragma ComponentBehavior: Bound

import qs
import qs.services
import qs.modules.common
import qs.modules.ii.plasmaCommon
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

/**
 * KDE Plasma 6 Digital Clock popup (calendar) recreated in Breeze Dark.
 * - Opened from the clock of the Plasma taskbar, anchored above it.
 * - Header: today's long date and the live time.
 * - Month view: month/year title, previous / "Hoy" / next, weekday names,
 *   ISO week numbers, days of the adjacent months dimmed, today highlighted.
 * - Mouse wheel over the grid changes month; Escape closes.
 * - IPC: quickshell -c ii ipc call plasmaCalendar toggle|open|close
 */
Scope {
    id: root

    readonly property bool opened: GlobalStates.plasmaCalendarOpen
    readonly property var locale: Qt.locale("es_ES")
    readonly property date today: DateTime.clock.date

    // First day of the month being shown
    property int viewYear: today.getFullYear()
    property int viewMonth: today.getMonth()

    function open() {
        GlobalStates.plasmaCalendarOpen = true;
    }
    function close() {
        GlobalStates.plasmaCalendarOpen = false;
    }
    function toggle() {
        GlobalStates.plasmaCalendarOpen = !GlobalStates.plasmaCalendarOpen;
    }

    function goToday() {
        root.viewYear = root.today.getFullYear();
        root.viewMonth = root.today.getMonth();
    }
    function shiftMonth(delta) {
        const d = new Date(root.viewYear, root.viewMonth + delta, 1);
        root.viewYear = d.getFullYear();
        root.viewMonth = d.getMonth();
    }

    function capitalize(text) {
        return text.length > 0 ? text.charAt(0).toUpperCase() + text.slice(1) : text;
    }

    // ISO 8601 week number
    function isoWeek(d) {
        const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
        const dayNum = t.getUTCDay() || 7;
        t.setUTCDate(t.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
        return Math.ceil(((t - yearStart) / 86400000 + 1) / 7);
    }

    // 6 weeks x 7 days starting on Monday, like Plasma's month view
    readonly property var days: {
        const first = new Date(root.viewYear, root.viewMonth, 1);
        const offset = (first.getDay() + 6) % 7; // Monday = 0
        const start = new Date(root.viewYear, root.viewMonth, 1 - offset);
        const list = [];
        for (let i = 0; i < 42; i++) {
            const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
            list.push({
                date: d,
                day: d.getDate(),
                inMonth: d.getMonth() === root.viewMonth,
                isToday: d.getFullYear() === root.today.getFullYear()
                    && d.getMonth() === root.today.getMonth()
                    && d.getDate() === root.today.getDate(),
                weekend: d.getDay() === 0 || d.getDay() === 6
            });
        }
        return list;
    }

    onOpenedChanged: if (opened) goToday()

    IpcHandler {
        target: "plasmaCalendar"
        function toggle(): void { root.toggle(); }
        function open(): void { root.open(); }
        function close(): void { root.close(); }
    }

    BreezePopupWindow {
        opened: root.opened
        anchorX: GlobalStates.plasmaCalendarAnchorX
        screenName: GlobalStates.plasmaCalendarScreen
        namespace: "quickshell:plasmaCalendar"
        popupWidth: 360
        popupHeight: 400
        onCloseRequested: root.close()

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 1
            spacing: 0

            // Today: long date + live clock
            BreezeHeader {
                Layout.preferredHeight: 56

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Text {
                        text: root.capitalize(root.locale.toString(root.today, "dddd"))
                        color: Breeze.text
                        font.family: Breeze.fontFamily
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Text {
                        text: root.locale.toString(root.today, "d 'de' MMMM 'de' yyyy")
                        color: Breeze.textMuted
                        font.family: Breeze.fontFamily
                        font.pixelSize: 12
                    }
                }
                Text {
                    Layout.rightMargin: 6
                    text: DateTime.time
                    color: Breeze.text
                    font.family: Breeze.fontFamily
                    font.pixelSize: 22
                    font.weight: Font.Light
                    font.features: { "tnum": 1 }
                }
            }

            // Month navigation
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 12
                Layout.rightMargin: 8
                Layout.topMargin: 8
                spacing: 4

                Text {
                    Layout.fillWidth: true
                    text: root.capitalize(root.locale.standaloneMonthName(root.viewMonth, Locale.LongFormat))
                        + ` ${root.viewYear}`
                    color: Breeze.text
                    font.family: Breeze.fontFamily
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
                BreezeToolButton {
                    implicitWidth: 28
                    iconSource: Breeze.icon("network", "go-up")
                    rotation: -90
                    onClicked: root.shiftMonth(-1)
                }
                BreezeToolButton {
                    label: "Hoy"
                    enabled: root.viewYear !== root.today.getFullYear() || root.viewMonth !== root.today.getMonth()
                    onClicked: root.goToday()
                }
                BreezeToolButton {
                    implicitWidth: 28
                    iconSource: Breeze.icon("network", "go-up")
                    rotation: 90
                    onClicked: root.shiftMonth(1)
                }
            }

            // Month grid
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 8

                WheelHandler {
                    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                    onWheel: event => root.shiftMonth(event.angleDelta.y > 0 ? -1 : 1)
                }

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    // Weekday names (Monday first) with an empty week-number corner
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 26
                        spacing: 0
                        Item { Layout.preferredWidth: 28 }
                        Repeater {
                            model: 7
                            delegate: Text {
                                required property int index
                                Layout.fillWidth: true
                                Layout.preferredWidth: 1
                                horizontalAlignment: Text.AlignHCenter
                                text: root.locale.dayName((index + 1) % 7, Locale.ShortFormat).replace(".", "")
                                color: Breeze.textMuted
                                font.family: Breeze.fontFamily
                                font.pixelSize: 11
                                font.capitalization: Font.Capitalize
                            }
                        }
                    }

                    // 6 weeks: ISO week number + 7 days
                    Repeater {
                        model: 6
                        delegate: RowLayout {
                            id: week
                            required property int index
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 0

                            Text {
                                Layout.preferredWidth: 28
                                horizontalAlignment: Text.AlignHCenter
                                text: root.isoWeek(root.days[week.index * 7].date)
                                color: Breeze.textMuted
                                opacity: 0.6
                                font.family: Breeze.fontFamily
                                font.pixelSize: 10
                            }

                            Repeater {
                                model: 7
                                delegate: MouseArea {
                                    id: dayMouse
                                    required property int index
                                    readonly property var info: root.days[week.index * 7 + index]
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    Layout.preferredWidth: 1
                                    hoverEnabled: true
                                    // Clicking a dimmed day of the adjacent month jumps to it
                                    onClicked: if (!info.inMonth) root.shiftMonth(info.date < new Date(root.viewYear, root.viewMonth, 1) ? -1 : 1)

                                    Rectangle {
                                        anchors.centerIn: parent
                                        width: Math.min(parent.width, parent.height) - 4
                                        height: width
                                        radius: 4
                                        color: dayMouse.info.isToday ? Breeze.accent : (dayMouse.containsMouse ? Breeze.hover : "transparent")
                                        border.width: dayMouse.containsMouse && !dayMouse.info.isToday ? 1 : 0
                                        border.color: Breeze.accentBorder
                                    }
                                    Text {
                                        anchors.centerIn: parent
                                        text: dayMouse.info.day
                                        color: dayMouse.info.isToday ? "#fcfcfc" : Breeze.text
                                        opacity: dayMouse.info.inMonth ? 1 : 0.35
                                        font.family: Breeze.fontFamily
                                        font.pixelSize: 13
                                        font.weight: dayMouse.info.isToday ? Font.DemiBold : Font.Normal
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
