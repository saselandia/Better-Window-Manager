//@ pragma Env QS_NO_RELOAD_POPUP=1
import Quickshell
import Quickshell.Io

// Compatibility entry point for old launch commands. Retro settings belong to
// OmarchyMenu; this file creates no window and immediately hands over to it.
Scope {
    Process {
        running: true
        command: ["qs", "-c", "ii", "ipc", "call", "omarchyMenu", "settings", Quickshell.env("SETTINGS_PAGE") || "all"]
        onExited: Qt.quit()
    }
}
