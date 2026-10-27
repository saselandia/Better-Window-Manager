pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import "SystemInfoData.js" as OsRelease

/**
 * Provides some system info: distro, username.
 */
Singleton {
    id: root
    property string distroName: "Linux"
    property string distroId: "unknown"
    property string distroIcon: "linux-symbolic"
    property string distroVersion: ""
    property bool distroReady: false
    property string username: "user"
    property string homeUrl: ""
    property string documentationUrl: ""
    property string supportUrl: ""
    property string bugReportUrl: ""
    property string privacyPolicyUrl: ""
    property string logo: ""
    property string desktopEnvironment: ""
    property string windowingSystem: ""

    function applyOsRelease(text) {
        const info = OsRelease.parse(text);
        root.distroName = info.PRETTY_NAME || info.NAME || "Linux";
        root.distroId = info.ID || "linux";
        root.distroVersion = info.VERSION || info.VERSION_ID || "";
        root.homeUrl = info.HOME_URL || "";
        root.documentationUrl = info.DOCUMENTATION_URL || "";
        root.supportUrl = info.SUPPORT_URL || "";
        root.bugReportUrl = info.BUG_REPORT_URL || "";
        root.privacyPolicyUrl = info.PRIVACY_POLICY_URL || "";
        root.distroIcon = OsRelease.icon(root.distroId, info.ID_LIKE);
        if (root.distroName.toLowerCase().includes("nyarch")) root.distroIcon = "nyarch-symbolic";
        root.logo = info.LOGO || root.distroIcon;
        root.distroReady = true;
    }

    Process {
        id: getUsername
        running: true
        command: ["whoami"]
        stdout: SplitParser {
            onRead: data => {
                root.username = data.trim()
            }
        }
    }

    Process {
        id: getDesktopEnvironment
        running: true
        command: ["bash", "-c", "echo $XDG_CURRENT_DESKTOP,$WAYLAND_DISPLAY"]
        stdout: StdioCollector {
            id: deCollector
            onStreamFinished: {
                const [desktop, wayland] = deCollector.text.split(",")
                root.desktopEnvironment = desktop.trim()
                root.windowingSystem = wayland.trim().length > 0 ? "Wayland" : "X11" // Are there others? 🤔
            }
        }
    }

    FileView {
        id: fileOsRelease
        path: "/etc/os-release"
        watchChanges: true
        printErrors: false
        onLoaded: root.applyOsRelease(text())
        onFileChanged: reload()
        onLoadFailed: error => {
            if (path !== "/usr/lib/os-release") path = "/usr/lib/os-release";
            else root.applyOsRelease("");
        }
    }
}
