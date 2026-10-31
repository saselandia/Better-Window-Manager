import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets

// Glass mode (glass.sh, port of Omarchy's glassy windows). default (end-4) shows it in General,
// Retro and Breeze (Kde plasma) in their Style page.
ContentSection {
    id: section
    icon: "blur_on"
    title: Translation.tr("Glass mode")

    readonly property string script: Quickshell.env("HOME") + "/.config/hypr/scripts/glass.sh"
    property bool glass: false

    Process {
        running: true
        command: [section.script, "status"]
        stdout: StdioCollector {
            onStreamFinished: section.glass = text.trim() === "on"
        }
    }

    ConfigSwitch {
        buttonIcon: "opacity"
        text: Translation.tr("Translucent windows with blur")
        checked: section.glass
        onClicked: {
            section.glass = !section.glass;
            Quickshell.execDetached([section.script, section.glass ? "on" : "off"]);
        }
        StyledToolTip {
            text: Translation.tr("Like Omarchy's glass mode: terminals at 65 %, dimmed GTK apps and\nfrosted blur behind the bar and menus. For every skin.")
        }
    }
}
