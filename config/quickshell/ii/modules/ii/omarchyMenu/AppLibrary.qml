import QtQuick
import Quickshell
import qs.services

// The app library omarchy-shell gives its menu (shell.appLibrary), on top of BWM's AppSearch:
// sorted desktop entries, names, subtitles, icons and launching. Terminal apps open in the
// default terminal (bwm-terminal). Uninstalling from the menu is not offered (Gentoo packages
// are not removed from a menu).
QtObject {
    id: root

    // The menu re-reads its Apps rows on this (new or removed desktop entries)
    signal appsChanged()
    readonly property var watchedList: AppSearch.list
    onWatchedListChanged: appsChanged()

    function entryById(appId) {
        return AppSearch.list.find(e => e.id === appId) ?? null;
    }
    function sortedEntries(query) {
        const list = Array.from(AppSearch.list);
        list.sort((a, b) => String(a.name).localeCompare(String(b.name)));
        return list.map(e => ({ entry: e }));
    }
    function entryName(entry) {
        return String(entry?.name ?? "");
    }
    function entrySubtext(entry) {
        return String(entry?.genericName || entry?.comment || "");
    }
    function iconSource(icon) {
        return Quickshell.iconPath(AppSearch.guessIcon(String(icon || "")), "image-missing");
    }
    function launch(appId, label) {
        const entry = root.entryById(appId);
        if (!entry)
            return;
        if (entry.runInTerminal && entry.command && entry.command.length > 0)
            Quickshell.execDetached([Quickshell.env("HOME") + "/.config/hypr/scripts/bwm-terminal", "--"].concat(Array.from(entry.command)));
        else
            entry.execute();
    }
    function remove(appId, label) {
        Quickshell.execDetached(["notify-send", "-a", "Menu", String(label || appId), "Uninstall it with your package manager (emerge --depclean / flatpak uninstall)."]);
    }
    function refreshIcons() {}
}
