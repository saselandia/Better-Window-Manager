pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

// Every ShellIpc handler, so the shell can answer an omarchy-shell call over
// its own socket instead of through a qs ipc client started per call. It
// answers only what qs ipc would: the first live, enabled handler for a
// target, and only the functions that handler declares. Those are allowed by
// name, never inferred from what a function call happens to reach: QObject
// methods such as destroy() are callable but not enumerable.
Singleton {
  id: root

  property var handlers: []

  // A bare handler's own functions (signals and hooks such as targetChanged),
  // which qs ipc never exposes and neither may the socket.
  readonly property var builtins: functionNames(bareHandler)

  IpcHandler {
    id: bareHandler
    enabled: false
  }

  function functionNames(object) {
    var names = []
    for (var key in object) {
      if (typeof object[key] === "function") names.push(key)
    }
    return names
  }

  // Bumped whenever a handler comes, goes or changes its target, so each
  // ShellIpc re-checks whether it leads its target.
  property int revision: 0

  function touch() {
    revision++
    Qt.callLater(root.reconcile)
  }

  function register(handler) {
    if (handlers.indexOf(handler) === -1) handlers.push(handler)
    touch()
  }

  function unregister(handler) {
    var index = handlers.indexOf(handler)
    if (index !== -1) handlers.splice(index, 1)
    touch()
  }

  // BWM: every bar has its own copy of a panel, so a call should reach the
  // copy on the focused monitor, not whichever registered first. A Panel
  // anchors its handlers to itself; its ipcScreenName says where it is.
  property var anchors: []

  function anchor(item, objects) {
    anchors = anchors.filter(function(entry) { return entry.item !== item }).concat([{ item: item, objects: objects }])
    touch()
  }

  function unanchor(item) {
    anchors = anchors.filter(function(entry) { return entry.item !== item })
    touch()
  }

  function screenOf(handler) {
    for (var i = 0; i < anchors.length; i++) {
      if (anchors[i].objects.indexOf(handler) !== -1) return anchors[i].item ? String(anchors[i].item.ipcScreenName || "") : ""
    }
    return ""
  }

  // Whether `handler` is the first live handler for its target. One with no
  // target, or not registered yet, doesn't lead, so it can't enable before
  // the registry knows of it. `revision` is there only to make a binding
  // re-check.
  function leads(handler, revision) {
    return leaderFor(handler.target) === handler
  }

  // BWM: Hyprland.focusedMonitor stays empty until focus first moves to
  // another monitor, so the focused output is read from hyprctl at start and
  // then followed through Hyprland's focusedmon events.
  property string focusedScreen: ""

  property Process focusedProc: Process {
    command: ["hyprctl", "-j", "activeworkspace"]
    running: true
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          root.focusedScreen = String(JSON.parse(text || "{}").monitor || "")
        } catch (e) {
          // hyprctl missing / Hyprland not running: keep Hyprland.focusedMonitor.
        }
        root.reconcile()
      }
    }
  }

  function currentScreen() {
    if (focusedScreen) return focusedScreen
    return Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : ""
  }

  // BWM: the copy on the focused monitor leads; without one, the first.
  function leaderFor(target) {
    if (!target) return null
    var focused = currentScreen()
    var first = null
    for (var i = 0; i < handlers.length; i++) {
      var other = handlers[i]
      if (!other || other.target !== target) continue
      if (!first) first = other
      if (focused && screenOf(other) === focused) return other
    }
    return first
  }

  // BWM: switched here rather than bound in ShellIpc, so the old leader has
  // let go of its target before the new one takes it (Quickshell warns that a
  // handler will not be used when both hold it, even for a moment).
  function reconcile() {
    for (var i = 0; i < handlers.length; i++) {
      var handler = handlers[i]
      if (handler && handler.enabled && leaderFor(handler.target) !== handler) handler.enabled = false
    }
    Qt.callLater(root.enableLeaders)
  }

  function enableLeaders() {
    for (var i = 0; i < handlers.length; i++) {
      var handler = handlers[i]
      if (!handler || handler.enabled || leaderFor(handler.target) !== handler) continue
      var taken = false
      for (var j = 0; j < handlers.length; j++) {
        var other = handlers[j]
        if (other && other !== handler && other.enabled && other.target === handler.target) taken = true
      }
      if (!taken) handler.enabled = true
    }
  }

  Connections {
    target: Hyprland
    function onFocusedMonitorChanged() {
      if (Hyprland.focusedMonitor) root.focusedScreen = Hyprland.focusedMonitor.name
      root.reconcile()
    }
    function onRawEvent(event) {
      var name = event ? String(event.name) : ""
      if (name !== "focusedmon" && name !== "focusedmonv2") return
      var screen = String(event.data || "").split(",")[0]
      if (screen && screen !== root.focusedScreen) {
        root.focusedScreen = screen
        root.reconcile()
      }
    }
  }

  function handlerFor(target) {
    for (var i = 0; i < handlers.length; i++) {
      var handler = handlers[i]
      if (handler && handler.enabled && handler.target === target) return handler
    }
    return null
  }

  // { ran: true, output } once the function ran; { ran: false } when it did
  // not (unknown target or function, wrong argument count), so the caller
  // can ask qs ipc for its exact answer without running anything twice.
  // The functions a handler declares: what it enumerates beyond a bare
  // handler, less property change signals.
  function declaredFunctions(handler) {
    return functionNames(handler).filter(function(name) {
      return builtins.indexOf(name) === -1 && !/Changed$/.test(name)
    })
  }

  function call(target, method, args) {
    var handler = handlerFor(target)
    if (!handler) return { ran: false }
    if (declaredFunctions(handler).indexOf(method) === -1) return { ran: false }
    if (handler[method].length !== args.length) return { ran: false }

    var result
    try {
      result = handler[method].apply(handler, args)
    } catch (error) {
      console.warn("ipc " + target + " " + method + " failed: " + error)
      return { ran: true, output: "" }
    }
    return { ran: true, output: result === undefined || result === null ? "" : String(result) }
  }
}
