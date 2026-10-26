import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import qs.Commons
import qs.Ui

// Omarchy's omarchy.workspaces widget (shell/plugins/bar/widgets/Workspaces.qml, MIT), with BWM's
// numbering: Omarchy gives each monitor a block of ten (1-10, 11-20…), BWM's workspaces are global,
// so every bar shows 1-5 and the other workspaces that exist on its own monitor, as Omarchy does
// inside its block (the 4K's workspace 10 does not show on the HP's bar).
// The one this monitor shows carries its layout glyph (a square tiles, a circle scrolls). BWM has
// no per-workspace layout switcher, so clicking it does nothing, as in Omarchy without one.
BarWidget {
  id: root
  moduleName: "omarchy.workspaces"

  // BWM parks minimized windows on workspace 99 (toggle-minimize.py): never a slot of its own
  readonly property int minimizedWorkspace: 99

  readonly property var monitor: {
    var window = root.QsWindow.window
    var screen = window ? window.screen : null
    return screen ? Hyprland.monitorFor(screen) : Hyprland.focusedMonitor
  }

  function activeWorkspaceId() {
    return root.monitor && root.monitor.activeWorkspace ? root.monitor.activeWorkspace.id : -1
  }

  function workspaceById(id) {
    var values = Hyprland.workspaces.values
    for (var i = 0; i < values.length; i++) {
      if (values[i].id === id) return values[i]
    }

    return null
  }

  // The first five, and any of the rest that exist on this monitor.
  function workspaceIds() {
    var ids = [1, 2, 3, 4, 5]
    var values = Hyprland.workspaces.values
    var monitorName = root.monitor ? root.monitor.name : ""

    for (var i = 0; i < values.length; i++) {
      var id = values[i].id
      if (id <= 0 || id === root.minimizedWorkspace) continue
      if (!values[i].monitor || values[i].monitor.name !== monitorName) continue
      if (ids.indexOf(id) === -1) ids.push(id)
    }

    ids.sort(function(left, right) { return left - right })
    return ids
  }

  function focusWorkspace(id) {
    Hyprland.dispatch("hl.dsp.focus({ workspace = " + id + " })")
  }

  // A wheel notch moves one entry along the row, and a touchpad adds up its
  // smaller deltas until they make a notch's worth.
  property real wheelAccumulator: 0

  function scrollWorkspaces(delta) {
    var wheel = Util.wheelSteps(root.wheelAccumulator, delta)
    root.wheelAccumulator = wheel.remainder
    if (wheel.steps === 0) return

    // Holds at either end rather than wrapping, so a touchpad swipe that runs
    // long stops on the last workspace.
    var ids = root.workspaceIds()
    var index = ids.indexOf(root.activeWorkspaceId())
    if (index === -1) return
    var target = ids[Util.clamp(index - wheel.steps, 0, ids.length - 1)]
    if (target !== ids[index]) root.focusWorkspace(target)
  }

  // Hyprland's global layout (dwindle/master tile, scrolling scrolls)
  property string activeMode: "dwindle"

  function modeGlyph(mode) {
    if (mode === "scrolling") return "󰝥"
    if (mode === "floating") return "󰔶"
    return "󱓻"
  }

  function readMode() {
    if (!modeProc.running) modeProc.running = true
  }

  Component.onCompleted: readMode()

  Connections {
    target: Hyprland
    function onRawEvent(event) {
      var name = event ? String(event.name) : ""
      if (name === "configreloaded") root.readMode()
      // Quickshell credits every workspace switch to the focused monitor, as
      // the event doesn't say which one switched, and misses the workspace a
      // monitor falls back to when its own is moved away. Moving workspaces
      // between monitors switches the others, so ask Hyprland for the truth.
      var switched = name === "workspacev2" && root.monitor !== null && root.monitor.focused
      if (switched || name === "moveworkspacev2" || name === "changeworkspaceid") {
        Hyprland.refreshMonitors()
        Hyprland.refreshWorkspaces()
      }
    }
  }

  Process {
    id: modeProc
    command: ["hyprctl", "getoption", "general:layout", "-j"]
    stdout: StdioCollector {
      onStreamFinished: {
        try {
          var mode = JSON.parse(text).str
          if (mode) root.activeMode = mode
        } catch (e) {}
      }
    }
  }

  readonly property real trailingGap: root.vertical ? 0 : Style.spaceReal(1.5)

  implicitWidth: grid.implicitWidth + trailingGap
  implicitHeight: grid.implicitHeight

  GridLayout {
    id: grid
    anchors.fill: parent
    anchors.rightMargin: root.trailingGap
    columns: root.vertical ? 1 : root.workspaceIds().length
    columnSpacing: root.vertical ? 0 : Style.space(1)
    rowSpacing: root.vertical ? Style.space(2) : 0

    Repeater {
      model: root.workspaceIds()

      WidgetButton {
        required property int modelData

        readonly property var workspace: root.workspaceById(modelData)
        readonly property bool occupied: workspace !== null && workspace.toplevels.values.length > 0
        readonly property bool shown: root.monitor !== null && root.monitor.activeWorkspace !== null && root.monitor.activeWorkspace.id === modelData

        bar: root.bar
        text: shown ? root.modeGlyph(root.activeMode) : (modelData === 10 ? "0" : String(modelData))
        opacity: occupied || shown ? 1 : 0.5
        horizontalMargin: 6
        verticalPadding: 6
        fixedWidth: root.vertical ? root.barSize : Style.space(20)
        fixedHeight: root.barSize
        onPressed: function() {
          if (!shown) root.focusWorkspace(modelData)
        }
        onWheelMoved: function(delta) { root.scrollWorkspaces(delta) }
      }
    }
  }
}
