"""Real task pointer events, isolated from the user's apps and shell.

BWM_RUN_QML_TESTS=1 python3 -m unittest discover -s tests -p test_plasma_task_input.py -v
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / 'config/quickshell/ii/modules/plasma/panel'

HARNESS = r'''//@ pragma UseQApplication
import QtQuick
import QtTest
import Quickshell
ShellRoot {
    id: root
    property var taskButton:null
    property int clicks: 0
    property int launches: 0
    property int contexts: 0
    property int cycles: 0
    property int activations: 0
    QtObject { id: fakeTop; property bool activated:false; property bool urgent:false; property string title:"Test window" }
    QtObject {
        id: adapter
        function click(group) { root.clicks++; }
        function launch(appId) { root.launches++; }
        function cycle(group, step) { root.cycles++; }
        function activate(window) { root.activations++; }
        function entry(appId) { return null; }
        function minimized(window) { return false; }
    }
    FloatingWindow {
        id: host
        title: "bwm-task-input-test"
        implicitWidth: 180; implicitHeight: 80
        ListView {
            anchors.fill:parent; orientation:ListView.Horizontal
            model:1
            delegate:Task {
                id: button; objectName:"taskButton"
                width:44; height:44
                edge:Quickshell.env("TASK_TEST_EDGE") || "bottom"
                group:({appId:"fixture",toplevels:[fakeTop]}); tasksModel:adapter
                Component.onCompleted:root.taskButton=this
                onContextRequested:root.contexts++
            }
        }
        TestCase { id: driver; name:"TaskInput"; when:false }
    }
    Timer { running:true; interval:4000; onTriggered:Qt.quit() }
    Timer {
        running:true; interval:500
        onTriggered: {
            const button=root.taskButton;
            const tooltip=driver.findChild(button,"taskTooltip");
            driver.mouseClick(button,22,22); // The actual icon, not the tooltip.
            driver.mouseClick(button,2,2); // Padding is clickable too.
            driver.mouseClick(button,22,22,Qt.MiddleButton);
            driver.mouseClick(button,22,22,Qt.RightButton);
            driver.mouseMove(button,22,22);
            driver.wait(20);
            driver.mouseWheel(button,22,22,0,120);
            driver.mousePress(button,22,22);
            driver.mouseMove(button,40,22,50);
            driver.mouseMove(button,65,22,50);
            driver.mouseRelease(button,65,22);
            driver.wait(50);
            const clicksAfterDrag=root.clicks;
            // Check the existing preview action still receives pointer input.
            tooltip.opened=true;
            driver.wait(100);
            driver.mouseClick(tooltip.contentItem,90,70);
            driver.wait(50);
            console.log("TASKRESULT "+JSON.stringify({clicks:root.clicks,clicksAfterDrag:clicksAfterDrag,launches:root.launches,contexts:root.contexts,cycles:root.cycles,activations:root.activations,previewClosed:!tooltip.opened}));
            Qt.quit();
        }
    }
}
'''

@unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS') == '1' and shutil.which('qs'),
                     'optional isolated QML pointer test')
class TaskInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(['hyprctl','eval',
                        'hl.window_rule({name="tmp-bwm-task-input",match={title="^bwm-task-input-test$"},workspace="9 silent"})'],
                       check=True,capture_output=True,text=True,timeout=5)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(['hyprctl','reload'],check=True,capture_output=True,text=True,timeout=5)

    def run_input_case(self, edge):
        with tempfile.TemporaryDirectory(prefix='bwm-task-input-') as folder:
            folder = Path(folder)
            task = (PANEL/'Task.qml').read_text().replace(
                'TaskToolTip {', 'TaskToolTip { objectName:"taskTooltip";')
            (folder/'Task.qml').write_text(task)
            shutil.copy(PANEL/'TaskPrefixes.js',folder)
            # Only capture is stubbed; the actual PopupWindow/card handlers are exercised.
            tooltip = (PANEL/'TaskToolTip.qml').read_text().replace(
                'ScreencopyView {', 'Item { property var captureSource; property bool live;')
            (folder/'TaskToolTip.qml').write_text(tooltip)
            # The tooltip resolves its frame with the theme's BlurPath; this harness checks
            # input, not the look: a stub keeps the variant used without blur.
            theme = folder/'modules/plasma/theme';theme.mkdir(parents=True)
            (theme/'qmldir').write_text('module qs.modules.plasma.theme\nBlurPath 1.0 BlurPath.qml\n')
            (theme/'BlurPath.qml').write_text('import QtQuick\nQtObject { required property string path; property string withoutBlur: path; readonly property string resolved: withoutBlur }\n')
            (folder/'test.qml').write_text(HARNESS)
            # No real task backend, IPC, or detached command may enter this harness.
            combined = task+tooltip+HARNESS
            self.assertNotIn('execDetached',combined)
            self.assertNotIn('Hyprland.dispatch',combined)
            self.assertNotIn('ipc call',combined)
            result = subprocess.run(['qs','-p',str(folder/'test.qml')],capture_output=True,
                                    text=True,timeout=10,env={**os.environ,'TASK_TEST_EDGE':edge})
            output = result.stdout+result.stderr
            self.assertEqual(result.returncode,0,output)
            for error in ['TypeError:', 'ReferenceError:', 'failed to load', 'is not a type']:
                self.assertNotIn(error,output)
            value = next((json.loads(line.split('TASKRESULT ',1)[1])
                          for line in output.splitlines() if 'TASKRESULT ' in line),None)
            self.assertEqual(value,dict(clicks=2,clicksAfterDrag=2,launches=1,contexts=1,
                                        cycles=1,activations=1,previewClosed=True),output)

    def test_icon_padding_buttons_drag_and_preview_on_all_edges(self):
        for edge in ('bottom','top','left','right'):
            with self.subTest(edge=edge):
                self.run_input_case(edge)

    def test_tooltip_thumbnail_guards_and_mpris_controls(self):
        harness = r'''
import QtQuick
import Quickshell
ShellRoot {
    id: root
    property int prevCount: 0
    property int toggleCount: 0
    property int nextCount: 0
    function findByName(item, name, out) {
        if (!item) return;
        if (item.objectName === name) out.push(item);
        const list = item.children || [];
        for (let i = 0; i < list.length; ++i) findByName(list[i], name, out);
    }
    QtObject {
        id: fakeModel
        function minimized(t) { return !!t?.isMin; }
        function entry(id) { return { icon: "spotify" }; }
        function activate(t) {}
    }
    QtObject {
        id: fakePlayer
        property string desktopEntry: "spotify"
        property string identity: "Spotify"
        property string dbusName: "org.mpris.MediaPlayer2.spotify"
        property string trackTitle: "Breeze Theme"
        property bool isPlaying: true
        property bool canPlay: true
        property bool canPause: true
        property bool canGoNext: true
        property bool canGoPrevious: true
        function previous() { root.prevCount++; }
        function togglePlaying() { root.toggleCount++; isPlaying = !isPlaying; }
        function next() { root.nextCount++; }
    }
    FloatingWindow {
        id: win
        title: "bwm-task-input-test"
        implicitWidth: 200; implicitHeight: 80; visible: true
        Item { id: anchorBox; width: 48; height: 48; property bool containsMouse: false }
        TaskToolTip {
            id: tip
            taskItem: anchorBox
            tasksModel: fakeModel
            group: ({
                appId: "spotify",
                toplevels: [
                    { title: "Visible", isMin: false },
                    { title: "Minimized", isMin: true }
                ]
            })
            mprisPlayers: [fakePlayer]
            opened: false
        }
        Timer {
            interval: 120; running: true
            onTriggered: {
                const thumbsClosed = [];
                root.findByName(tip.contentItem, "taskThumb", thumbsClosed);
                const closedAllNull = thumbsClosed.every(t => t.captureSource === null && !t.live);
                tip.opened = true;
                openCheck.start();
                root._closedAllNull = closedAllNull;
            }
        }
        Timer {
            id: openCheck; interval: 120
            onTriggered: {
                const thumbs = [], rows = [], labels = [], prevs = [], toggles = [], nexts = [];
                root.findByName(tip.contentItem, "taskThumb", thumbs);
                root.findByName(tip.contentItem, "mediaRow", rows);
                root.findByName(tip.contentItem, "mediaTrackLabel", labels);
                root.findByName(tip.contentItem, "mediaPrev", prevs);
                root.findByName(tip.contentItem, "mediaToggle", toggles);
                root.findByName(tip.contentItem, "mediaNext", nexts);
                const visOk = thumbs.length === 2
                    && thumbs[0].captureSource !== null && thumbs[0].live === true
                    && thumbs[1].captureSource === null && thumbs[1].live === false;
                const mediaVis = rows.length > 0 && rows[0].visible === true;
                const track = labels.length > 0 ? labels[0].text : "";
                if (prevs.length > 0) prevs[0].clicked();
                if (toggles.length > 0) toggles[0].clicked();
                if (nexts.length > 0) nexts[0].clicked();
                tip.opened = false;
                const reopenedNull = thumbs.every(t => t.captureSource === null && !t.live);
                console.log("THUMBRESULT " + JSON.stringify({
                    closedAllNull: root._closedAllNull,
                    visOk: visOk,
                    mediaVis: mediaVis,
                    track: track,
                    prev: root.prevCount,
                    toggle: root.toggleCount,
                    next: root.nextCount,
                    reopenedNull: reopenedNull
                }));
                Qt.quit();
            }
        }
    }
    property bool _closedAllNull: false
}
'''
        with tempfile.TemporaryDirectory(prefix='bwm-task-thumb-') as folder:
            folder = Path(folder)
            tooltip = (PANEL/'TaskToolTip.qml').read_text().replace(
                'ScreencopyView {', 'Item { property var captureSource; property bool live;')
            (folder/'TaskToolTip.qml').write_text(tooltip)
            theme = folder/'modules/plasma/theme'; theme.mkdir(parents=True)
            (theme/'qmldir').write_text('module qs.modules.plasma.theme\nBlurPath 1.0 BlurPath.qml\n')
            (theme/'BlurPath.qml').write_text('import QtQuick\nQtObject { required property string path; property string withoutBlur: path; readonly property string resolved: withoutBlur }\n')
            (folder/'test.qml').write_text(harness)
            result = subprocess.run(['qs','-p',str(folder/'test.qml')],capture_output=True,text=True,timeout=10)
            output = result.stdout+result.stderr
            self.assertEqual(result.returncode,0,output)
            for error in ['TypeError:', 'ReferenceError:', 'failed to load', 'is not a type']:
                self.assertNotIn(error,output)
            value = next((json.loads(line.split('THUMBRESULT ',1)[1])
                          for line in output.splitlines() if 'THUMBRESULT ' in line),None)
            self.assertEqual(value,dict(
                closedAllNull=True,visOk=True,mediaVis=True,track="Breeze Theme",
                prev=1,toggle=1,next=1,reopenedNull=True),output)

