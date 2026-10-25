import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets

// Default applications, shared by every theme: terminal, browser, file manager, text editor and
// task manager. Backend: hypr/scripts/default-apps.py (xdg-mime / xdg-settings, Quickshell's
// apps.terminal / apps.taskManager, ~/.config/bwm/default-apps.json for bwm-terminal).
ContentPage {
    id: page
    forceWidth: true

    readonly property string script: Quickshell.env("HOME") + "/.config/hypr/scripts/default-apps.py"
    property var data: ({})
    readonly property var kinds: [
        { kind: "terminal", icon: "terminal", title: Translation.tr("Terminal"),
          hint: Translation.tr("Used by the task manager, Omarchy plugins and shell actions") },
        { kind: "browser", icon: "language", title: Translation.tr("Web browser"), hint: "" },
        { kind: "files", icon: "folder", title: Translation.tr("File manager"), hint: "" },
        { kind: "editor", icon: "edit_note", title: Translation.tr("Text editor"), hint: "" },
        { kind: "taskmanager", icon: "monitoring", title: Translation.tr("Task manager"),
          hint: Translation.tr("Terminal programs (btop, htop) open in the default terminal") }
    ]

    Process {
        id: listProc
        running: true
        command: ["python3", page.script, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    page.data = JSON.parse(text);
                } catch (e) {}
            }
        }
    }
    Process {
        id: setProc
        onExited: listProc.running = true
    }

    Repeater {
        model: page.kinds
        delegate: ContentSection {
            id: section
            required property var modelData
            readonly property var info: page.data[modelData.kind] ?? { current: "", options: [] }
            readonly property var options: {
                // The current choice always shows, even if it is not in the detected list
                const opts = (info.options ?? []).slice();
                if (info.current && !opts.some(o => o.id === info.current))
                    opts.unshift({ id: info.current, name: info.current });
                return opts;
            }
            icon: modelData.icon
            title: modelData.title

            StyledText {
                visible: section.modelData.hint !== ""
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                color: Appearance.colors.colSubtext
                text: section.modelData.hint
            }

            StyledComboBox {
                Layout.fillWidth: true
                implicitHeight: 40
                enabled: section.options.length > 0
                textRole: "name"
                model: section.options
                currentIndex: section.options.findIndex(o => o.id === section.info.current)
                displayText: section.options.length > 0 ? currentText : Translation.tr("None installed")
                onActivated: index => {
                    setProc.command = ["python3", page.script, "set", section.modelData.kind, section.options[index].id];
                    setProc.running = true;
                }
            }
        }
    }
}
