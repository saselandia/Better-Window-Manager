// BWM: host for upstream digital-clock/CalendarView.qml with local time and KDE calendar data.
// Time zone list, current zone and offsets follow digital-clock/main.qml 6.7.5
// (GPL-2.0-or-later), reading the native keys kept in bar.plasma.clock.
import QtQuick
import org.kde.plasma.clock
import org.kde.plasma.private.digitalclock
import qs.modules.common
import ".."
AppletHost {
    id:root
    translationDomain:"plasma_applet_org.kde.plasma.digitalclock"
    readonly property var clockSettings:Config.options?.bar?.plasma?.clock ?? ({})
    readonly property var selectedTimeZones:Array.isArray(clockSettings.selectedTimeZones)&&clockSettings.selectedTimeZones.length>0
        ? clockSettings.selectedTimeZones : ["Local"]
    readonly property date currentTime:currentClock.dateTime
    readonly property string currentTimeZone:currentClock.timeZone
    configuration: QtObject {
        property var enabledCalendarPlugins:Array.isArray(root.clockSettings.enabledCalendarPlugins) ? root.clockSettings.enabledCalendarPlugins : []
        property int displayTimezoneFormat:root.clockSettings.displayTimezoneFormat ?? 1
        property int showSeconds:root.clockSettings.showSeconds ?? 0
        property int firstDayOfWeek:root.clockSettings.firstDayOfWeek ?? -1
        property bool showWeekNumbers:root.clockSettings.showWeekNumbers ?? true
        property bool pin:false
    }
    Clock { id:currentClock; timeZone:root.clockSettings.lastSelectedTimezone || "Local" }
    // not defining a timezone keeps it up to date with the system timezone
    Clock { id:systemClock }
    function selectedTimeZonesDeduplicatingExplicitLocalTimeZone() {
        // Upstream: hide an explicit entry that resolves to the current local zone.
        const isLiterallyLocalOrResolvesToSomethingOtherThanLocal = timeZone =>
            timeZone == "Local" || timeZone != systemClock.timeZone
        return TimeZoneUtils.sortedTimeZones(root.selectedTimeZones
            .filter(isLiterallyLocalOrResolvesToSomethingOtherThanLocal));
    }
    function formatTime(date,seconds) {
        let formatted=Qt.formatTime(date, seconds?"hh:mm:ss":Qt.locale().timeFormat(Locale.ShortFormat));
        if (date.getDay() !== currentClock.dateTime.getDay())
            formatted += " " + Qt.locale().toString(date, "dddd");
        return formatted;
    }
    function formatOffset(dateTime) {
        const offset = Math.round((dateTime - currentClock.dateTime) / (1000 * 60));
        if (offset === 0) return "";
        const absoluteOffset = Math.abs(offset);
        const hourOffset = Math.floor(absoluteOffset / 60);
        const minuteOffset = absoluteOffset % 60;
        if (offset > 0) {
            return minuteOffset === 0
                ? root.i18ncp("@info offset from current time", " • %1 hour later", " • %1 hours later", hourOffset)
                : root.i18nc("@info offset from current time in hours and minutes", " • %1:%2 later", hourOffset, minuteOffset);
        }
        return minuteOffset === 0
            ? root.i18ncp("@info offset from current time", " • %1 hour earlier", " • %1 hours earlier", hourOffset)
            : root.i18nc("@info offset from current time in hours and minutes", " • %1:%2 earlier", hourOffset, minuteOffset);
    }
    fullRepresentation: CalendarView {}
}
