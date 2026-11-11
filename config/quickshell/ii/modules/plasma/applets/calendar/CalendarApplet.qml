// BWM: host for upstream digital-clock/CalendarView.qml with local time and KDE calendar data.
import QtQuick
import org.kde.plasma.clock
import ".."
AppletHost {
    id:root
    translationDomain:"plasma_applet_org.kde.plasma.digitalclock"
    readonly property date currentTime:clock.dateTime
    property string currentTimeZone:"Local"
    configuration: QtObject {
        property var enabledCalendarPlugins:[]
        property int displayTimezoneFormat:1
        property int showSeconds:0
        property int firstDayOfWeek:-1
        property bool showWeekNumbers:true
        property bool pin:false
    }
    Clock { id:clock; timeZone:root.currentTimeZone }
    function selectedTimeZonesDeduplicatingExplicitLocalTimeZone() { return ["Local"]; }
    function formatTime(date,seconds) { return Qt.formatTime(date, seconds?"hh:mm:ss":Qt.locale().timeFormat(Locale.ShortFormat)); }
    function formatOffset(date) { return ""; }
    fullRepresentation: CalendarView {}
}
