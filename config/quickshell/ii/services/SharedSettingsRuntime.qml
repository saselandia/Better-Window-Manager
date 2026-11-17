// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import Quickshell
import Quickshell.Io

// One instance in the main shell, outside skin/panel loaders. No preference IO.
Scope {
    id: root
    required property bool ready
    required property int workspaceCount
    required property string skin
    required property var dispatcherCommand
    readonly property bool busy: dispatcher.running
    property int completedPasses: 0
    property var lastReport: ({})
    property bool _attempt: false
    property bool _pending: false
    signal passFinished(var report)

    function schedule() {
        if (!ready) return;
        if (_attempt) { _pending = true; return; }
        delivery.interval = 200;
        delivery.restart();
    }
    function launch() {
        if (!ready || _attempt) return;
        _pending = false;
        _attempt = true;
        dispatcher.command = dispatcherCommand;
        dispatcher.running = true;
    }
    function finish(code) {
        if (!_attempt) return;
        _attempt = false;
        let report = { version: 1, retryMs: 5000, error: "Shared settings dispatcher failed" };
        if (code === 0) {
            try {
                const value = JSON.parse(output.text);
                if (value.version === 1 && Number.isInteger(value.retryMs)
                    && (value.retryMs === 0 || (value.retryMs >= 1000 && value.retryMs <= 30000))) report = value;
            } catch (error) {}
        }
        lastReport = report;
        completedPasses++;
        if (ready) {
            if (_pending) schedule();
            else if (report.retryMs > 0) {
                delivery.interval = report.retryMs;
                delivery.restart();
            }
        }
        passFinished(report);
    }
    onReadyChanged: {
        if (ready) schedule();
        else { delivery.stop(); _pending = false; }
    }
    onWorkspaceCountChanged: schedule()
    onSkinChanged: schedule()
    onDispatcherCommandChanged: schedule()
    Component.onCompleted: schedule()

    Timer { id: delivery; onTriggered: root.launch() }
    IpcHandler {
        target: "sharedSettings"
        function status(): string {
            return JSON.stringify({version:1,ready:root.ready,busy:root.busy,
                completedPasses:root.completedPasses,skin:root.skin,lastReport:root.lastReport});
        }
    }
    Process {
        id: dispatcher
        stdout: StdioCollector { id: output }
        onExited: (code, status) => root.finish(code)
        // Quickshell emits no exited() for FailedToStart. Do not leave the
        // coordinator permanently busy; source ordering is covered in tests.
        onRunningChanged: {
            if (!running && root._attempt) Qt.callLater(function() {
                if (!dispatcher.running && root._attempt) root.finish(-1);
            });
        }
    }
}
