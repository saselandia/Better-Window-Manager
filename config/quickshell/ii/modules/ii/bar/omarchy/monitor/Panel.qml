import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import qs.Ui
import qs.Commons
import qs.Commons as Commons
import "Model.js" as Model

Panel {
  id: root
  moduleName: "omarchy.monitor"
  ipcTarget: "omarchy.monitor"
  manageIpc: false

  property var monitors: []
  property string focusedMonitor: ""
  property string primaryMonitor: ""
  property string selectedMonitorName: ""

  readonly property var selectedMonitor: {
    for (var i = 0; i < monitors.length; i++) {
      if (monitors[i].name === selectedMonitorName) return monitors[i]
    }
    return monitors.length > 0 ? monitors[0] : null
  }

  // Brightness per monitor name (a new object on every change so bindings see it)
  property var brightness: ({})
  property bool brightnessDragging: false
  readonly property int selectedBrightness: selectedMonitor && brightness[selectedMonitor.name] !== undefined
    ? brightness[selectedMonitor.name] : 100
  readonly property string managerScript: Quickshell.env("HOME") + "/.config/hypr/scripts/monitor-manager.py"

  property bool nightlightEnabled: false
  property int nightlightTemp: 4000

  // Text size slider
  readonly property var textSizeStops: [9, 10, 11, 12, 14, 16, 20]
  property int textSizePreviewIndex: -1
  property bool reflowingText: false

  function markReflowing() {
    root.reflowingText = true
    reflowSettle.restart()
  }

  // Common scaling presets
  readonly property var scalePresets: ["1", "1.25", "1.5", "1.6", "2"]

  // Refresh monitors and nightlight state
  function refresh() {
    if (!stateProc.running) stateProc.running = true
  }

  Process {
    id: stateProc
    command: ["omarchy-monitor-state", "--json"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var data = JSON.parse(text)
          root.monitors = data.monitors || []
          if (!root.brightnessDragging && !brightnessApplyTimer.running && !brightnessActionProc.running) {
            var b = {}
            for (var i = 0; i < root.monitors.length; i++)
              b[root.monitors[i].name] = root.monitors[i].brightness !== undefined ? root.monitors[i].brightness : 100
            root.brightness = b
          }
          root.focusedMonitor = data.focused || ""
          root.primaryMonitor = data.primary || ""

          if (data.nightlight) {
            root.nightlightEnabled = !!data.nightlight.enabled
            if (data.nightlight.temperature) root.nightlightTemp = data.nightlight.temperature
          }

          // If no monitor selected yet, pick focused or first
          if (!root.selectedMonitorName || !root.selectedMonitor) {
            root.selectedMonitorName = root.focusedMonitor || (root.monitors.length > 0 ? root.monitors[0].name : "")
          }
        } catch(e) {
          console.warn("Failed to parse monitor state JSON:", e)
        }
      }
    }
  }

  // Night light actions
  Process {
    id: nightlightActionProc
    onRunningChanged: if (!running) root.refresh()
  }

  function toggleNightlight(on) {
    root.nightlightEnabled = on
    nightlightActionProc.command = ["omarchy-toggle-nightlight"]
    nightlightActionProc.running = true
  }

  function setNightlightTemperature(temp) {
    root.nightlightTemp = temp
    if (root.nightlightEnabled) {
      nightlightActionProc.command = ["omarchy-toggle-nightlight", String(temp)]
      nightlightActionProc.running = true
    }
  }

  // Monitor management actions
  Process {
    id: monitorActionProc
    onRunningChanged: if (!running) root.refresh()
  }

  // Only chooses which monitor the settings below apply to (no focus change)
  function selectMonitor(name) {
    root.selectedMonitorName = name
  }

  function setMonitorScale(name, scale) {
    monitorActionProc.command = ["python3", root.managerScript, "set-scale", name, String(scale)]
    monitorActionProc.running = true
  }

  function setMonitorMode(name, res, hz) {
    var cmd = ["python3", root.managerScript, "set-mode", name, res]
    if (hz) cmd.push(String(hz))
    monitorActionProc.command = cmd
    monitorActionProc.running = true
  }

  function setMonitorTransform(name, tr) {
    monitorActionProc.command = ["python3", root.managerScript, "set-transform", name, String(tr)]
    monitorActionProc.running = true
  }

  function setMonitorPrimary(name) {
    monitorActionProc.command = ["python3", root.managerScript, "set-primary", name]
    monitorActionProc.running = true
  }

  function toggleMonitorEnable(name) {
    monitorActionProc.command = ["python3", root.managerScript, "toggle-enable", name]
    monitorActionProc.running = true
  }

  // Individual brightness setters
  Process {
    id: brightnessActionProc
  }

  property var pendingBrightness: ({})

  Timer {
    id: brightnessApplyTimer
    interval: 150
    repeat: false
    onTriggered: {
      if (brightnessActionProc.running) { restart(); return }
      // Every pending monitor in one go (one Process runs one command at a time)
      var script = ""
      var args = []
      for (var mon in root.pendingBrightness) {
        args.push(mon, String(root.pendingBrightness[mon]))
        script += 'omarchy-brightness-display --no-osd --monitor "$' + (args.length - 1) + '" "$' + args.length + '%";'
      }
      root.pendingBrightness = {}
      if (args.length === 0) return
      brightnessActionProc.command = ["bash", "-c", script, "bash"].concat(args)
      brightnessActionProc.running = true
    }
  }

  function setBrightness(monName, val) {
    if (!monName) return
    var percent = Math.max(1, Math.min(100, Math.round(val)))
    var next = Object.assign({}, root.brightness)
    next[monName] = percent
    root.brightness = next            // the UI follows at once
    root.pendingBrightness[monName] = percent
    brightnessApplyTimer.restart()    // DDC is slow: apply after a short pause
  }

  // Text size actions
  Process {
    id: textScaleProc
    stdout: StdioCollector { waitForEnd: true }
  }

  Timer {
    id: reflowSettle
    interval: 300
    repeat: false
    onTriggered: root.reflowingText = false
  }

  function nearestTextStop(px) {
    var best = 0
    var bestDist = 1e9
    for (var i = 0; i < textSizeStops.length; i++) {
      var d = Math.abs(textSizeStops[i] - px)
      if (d < bestDist) { bestDist = d; best = i }
    }
    return best
  }

  function currentTextIndex() {
    return textSizePreviewIndex >= 0 ? textSizePreviewIndex : nearestTextStop(Style.font.baseSize)
  }

  function displayedTextPx() {
    return textSizePreviewIndex >= 0 ? textSizeStops[textSizePreviewIndex] : Style.font.baseSize
  }

  function setTextSize(px) {
    textScaleProc.command = ["omarchy-display-text-size", String(px)]
    if (!textScaleProc.running) textScaleProc.running = true
  }

  Connections {
    target: Style
    function onFontBaseSizeChanged() {
      root.markReflowing()
      if (root.textSizePreviewIndex >= 0
          && root.nearestTextStop(Style.font.baseSize) === root.textSizePreviewIndex)
        root.textSizePreviewIndex = -1
    }
  }

  // IPC
  ShellIpc {
    target: "omarchy.monitor"
    function open(): void { root.open() }
    function close(): void { root.close() }
    function toggle(): void { root.toggle() }
    function show(): void { root.open() }
    function hide(): void { root.close() }
    function refresh(): void { root.refresh() }
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Component.onCompleted: refresh()

  onOpenedChanged: {
    if (opened) refresh()
  }

  Timer {
    interval: 8000
    running: root.opened
    repeat: true
    onTriggered: root.refresh()
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.monitors.length > 1 ? "󰍺" : "󰍹"
    onPressed: function(b) { root.toggle() }
    // Wheel over the icon: brightness of the monitor this bar is on
    onWheelMoved: function(delta) {
      var name = root.QsWindow.window && root.QsWindow.window.screen ? root.QsWindow.window.screen.name : root.focusedMonitor
      var cur = root.brightness[name] !== undefined ? root.brightness[name] : 100
      root.setBrightness(name, cur + (delta > 0 ? 5 : -5))
    }
  }

  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened === true
    focusTarget: panel.loadedContent
    contentWidth: panel.fittedContentWidth(Style.space(420))
    contentHeight: panel.fittedContentHeight(panel.loadedContentHeight, Style.space(640))

    content: PanelKeyCatcher {
      id: keyCatcher
      implicitHeight: panelColumn.implicitHeight
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }

      ScrollView {
        id: scrollArea
        anchors.fill: parent
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical.policy: panelColumn.implicitHeight > height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff

        Column {
          id: panelColumn
          width: scrollArea.availableWidth
          spacing: Style.space(14)

          // ---------- Hero ----------
          Item {
            width: parent.width
            implicitHeight: Math.max(heroIcon.implicitHeight, heroLabels.implicitHeight)

            Text {
              id: heroIcon
              textFormat: Text.PlainText
              text: root.monitors.length > 1 ? "󰍺" : "󰍹"
              color: root.bar.foreground
              font.family: root.bar.fontFamily
              font.pixelSize: Style.font.display
              anchors.left: parent.left
              anchors.verticalCenter: parent.verticalCenter
            }

            Column {
              id: heroLabels
              anchors.left: heroIcon.right
              anchors.leftMargin: Style.space(14)
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              spacing: Style.space(2)

              Text {
                text: Commons.I18n.t("monitor.display") || "Pantallas"
                textFormat: Text.PlainText
                color: root.bar.foreground
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.title
                font.bold: true
                elide: Text.ElideRight
                width: parent.width
              }

              Text {
                id: heroLabel
                textFormat: Text.PlainText
                text: {
                  if (root.monitors.length === 0) return "Buscando pantallas..."
                  if (root.monitors.length === 1) return root.monitors[0].model + " (" + root.monitors[0].width + "x" + root.monitors[0].height + ")"
                  return root.monitors.length + " PANTALLAS CONECTADAS"
                }
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
                font.letterSpacing: 1.2
                elide: Text.ElideRight
                width: parent.width
              }
            }
          }

          // ---------- Monitor Selector Cards / Tabs ----------
          PanelSeparator {
            visible: root.monitors.length > 1
            foreground: root.bar.foreground
          }

          Column {
            width: parent.width
            spacing: Style.space(8)
            visible: root.monitors.length > 1

            PanelSectionHeader {
              text: "Seleccionar pantalla a configurar"
              foreground: root.bar.foreground
              fontFamily: root.bar.fontFamily
            }

            Row {
              width: parent.width
              spacing: Style.space(8)

              Repeater {
                model: root.monitors

                // Own tab: qs.Ui Button only sizes itself from its `text`
                Rectangle {
                  id: monTab
                  required property var modelData
                  required property int index
                  readonly property bool active: root.selectedMonitorName === modelData.name

                  width: (parent.width - (root.monitors.length - 1) * Style.space(8)) / Math.max(1, root.monitors.length)
                  height: tabColumn.implicitHeight + Style.space(16)
                  color: active ? Qt.rgba(Commons.Color.accent.r, Commons.Color.accent.g, Commons.Color.accent.b, 0.16)
                    : (tabMouse.containsMouse ? Qt.rgba(root.bar.foreground.r, root.bar.foreground.g, root.bar.foreground.b, 0.06) : "transparent")
                  border.width: 1
                  border.color: active ? Commons.Color.accent : Qt.rgba(root.bar.foreground.r, root.bar.foreground.g, root.bar.foreground.b, 0.35)

                  Column {
                    id: tabColumn
                    anchors.centerIn: parent
                    width: parent.width - Style.space(12)
                    spacing: Style.space(3)

                    Text {
                      width: parent.width
                      horizontalAlignment: Text.AlignHCenter
                      text: "󰍹  " + (monTab.modelData.model || monTab.modelData.name)
                      color: monTab.active ? Commons.Color.accent : root.bar.foreground
                      font.family: root.bar.fontFamily
                      font.pixelSize: Style.font.caption
                      font.bold: true
                      elide: Text.ElideRight
                    }
                    Text {
                      width: parent.width
                      horizontalAlignment: Text.AlignHCenter
                      text: (monTab.modelData.is_primary ? "★ " : "") + monTab.modelData.width + "x" + monTab.modelData.height
                        + " @ " + Math.round(monTab.modelData.refreshRate) + " Hz"
                      color: Qt.darker(root.bar.foreground, 1.4)
                      font.family: root.bar.fontFamily
                      font.pixelSize: Style.font.caption
                      elide: Text.ElideRight
                    }
                  }

                  MouseArea {
                    id: tabMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.selectMonitor(monTab.modelData.name)
                  }
                }
              }
            }
          }

          // ---------- Display Specific Controls (Scale, Resolution, Refresh, Orientation) ----------
          PanelSeparator {
            visible: root.selectedMonitor !== null
            foreground: root.bar.foreground
          }

          Column {
            width: parent.width
            spacing: Style.space(12)
            visible: root.selectedMonitor !== null

            // Section title showing selected monitor
            Row {
              spacing: Style.space(6)
              PanelSectionHeader {
                text: "Ajustes de " + (root.selectedMonitor ? (root.selectedMonitor.model || root.selectedMonitor.name) : "")
                foreground: root.bar.foreground
                fontFamily: root.bar.fontFamily
              }
              Text {
                text: "(" + (root.selectedMonitor ? root.selectedMonitor.name : "") + ")"
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                anchors.verticalCenter: parent.verticalCenter
              }
            }

            // 0. Brightness of this monitor (DDC/CI or backlight)
            Column {
              width: parent.width
              spacing: Style.space(6)

              Item {
                width: parent.width
                implicitHeight: brightnessLabel.implicitHeight
                Text {
                  id: brightnessLabel
                  text: "Brillo"
                  color: Qt.darker(root.bar.foreground, 1.4)
                  font.family: root.bar.fontFamily
                  font.pixelSize: Style.font.caption
                  font.bold: true
                }
                Text {
                  anchors.right: parent.right
                  anchors.rightMargin: Style.space(6)
                  text: Math.round(brightnessSlider.dragging ? brightnessSlider.liveValue : root.selectedBrightness) + "%"
                  color: Qt.darker(root.bar.foreground, 1.4)
                  font.family: root.bar.fontFamily
                  font.pixelSize: Style.font.caption
                  font.bold: true
                }
              }

              CursorSurface {
                width: parent.width
                height: brightnessSlider.implicitHeight + Style.spacing.controlGap
                foreground: root.bar.foreground
                outline: true

                PanelSlider {
                  id: brightnessSlider
                  bar: root.bar
                  anchors.fill: parent
                  anchors.leftMargin: Style.space(6)
                  anchors.rightMargin: Style.space(6)
                  minimum: 1
                  maximum: 100
                  step: 1
                  integer: true
                  value: root.selectedBrightness
                  onDraggingChanged: root.brightnessDragging = dragging
                  onReleased: function(v) { if (root.selectedMonitor) root.setBrightness(root.selectedMonitor.name, v) }
                }
              }
            }

            // 1. Fractional Scale
            Column {
              width: parent.width
              spacing: Style.space(6)

              Text {
                text: "Escalado de pantalla"
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
              }

              Grid {
                id: scaleRow
                width: parent.width
                columns: root.scalePresets.length
                spacing: Style.spacing.xs

                readonly property real cellWidth: (width - spacing * (columns - 1)) / columns

                Repeater {
                  model: root.scalePresets

                  Button {
                    required property string modelData
                    required property int index

                    width: scaleRow.cellWidth
                    text: modelData + "x"
                    fontSize: Style.font.caption
                    foreground: root.bar.foreground
                    fontFamily: root.bar.fontFamily
                    horizontalPadding: Style.spacing.sm
                    verticalPadding: Style.spacing.controlPaddingY
                    bordered: true
                    active: root.selectedMonitor && Math.abs(root.selectedMonitor.scale - parseFloat(modelData)) < 0.05

                    onClicked: {
                      if (root.selectedMonitor) {
                        root.setMonitorScale(root.selectedMonitor.name, modelData)
                      }
                    }
                  }
                }
              }
            }

            // 2. Resolution
            Column {
              width: parent.width
              spacing: Style.space(6)
              visible: root.selectedMonitor && root.selectedMonitor.resolutions && root.selectedMonitor.resolutions.length > 0

              Text {
                text: "Resolución"
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
              }

              Flow {
                width: parent.width
                spacing: Style.space(6)

                Repeater {
                  // Show top 4 resolutions for convenience
                  model: root.selectedMonitor ? root.selectedMonitor.resolutions.slice(0, 4) : []

                  Button {
                    required property string modelData
                    required property int index

                    text: modelData
                    fontSize: Style.font.caption
                    foreground: root.bar.foreground
                    fontFamily: root.bar.fontFamily
                    horizontalPadding: Style.spacing.sm
                    verticalPadding: Style.spacing.controlPaddingY
                    bordered: true
                    active: root.selectedMonitor && (root.selectedMonitor.width + "x" + root.selectedMonitor.height) === modelData

                    onClicked: {
                      if (root.selectedMonitor) {
                        root.setMonitorMode(root.selectedMonitor.name, modelData, null)
                      }
                    }
                  }
                }
              }
            }

            // 3. Refresh Rate (Hz)
            Column {
              id: rateSection
              width: parent.width
              spacing: Style.space(6)
              readonly property var curRes: root.selectedMonitor ? (root.selectedMonitor.width + "x" + root.selectedMonitor.height) : ""
              readonly property var availableRates: (root.selectedMonitor && root.selectedMonitor.modesMap && root.selectedMonitor.modesMap[curRes]) ? root.selectedMonitor.modesMap[curRes] : []
              visible: availableRates.length > 1

              Text {
                text: "Tasa de refresco (" + rateSection.curRes + ")"
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
              }

              Flow {
                width: parent.width
                spacing: Style.space(6)

                Repeater {
                  model: rateSection.availableRates

                  Button {
                    required property var modelData
                    required property int index

                    text: modelData + " Hz"
                    fontSize: Style.font.caption
                    foreground: root.bar.foreground
                    fontFamily: root.bar.fontFamily
                    horizontalPadding: Style.spacing.sm
                    verticalPadding: Style.spacing.controlPaddingY
                    bordered: true
                    active: root.selectedMonitor && Math.abs(root.selectedMonitor.refreshRate - modelData) < 0.2

                    onClicked: {
                      if (root.selectedMonitor) {
                        root.setMonitorMode(root.selectedMonitor.name, rateSection.curRes, modelData)
                      }
                    }
                  }
                }
              }
            }

            // 4. Orientation
            Column {
              width: parent.width
              spacing: Style.space(6)

              Text {
                text: "Orientación"
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
              }

              Row {
                width: parent.width
                spacing: Style.space(6)

                readonly property var orientations: [
                  { label: "Normal (0°)", val: 0 },
                  { label: "90°", val: 1 },
                  { label: "180°", val: 2 },
                  { label: "270°", val: 3 }
                ]

                Repeater {
                  model: parent.orientations

                  Button {
                    required property var modelData
                    required property int index

                    width: (parent.width - 3 * Style.space(6)) / 4
                    text: modelData.label
                    fontSize: Style.font.caption
                    foreground: root.bar.foreground
                    fontFamily: root.bar.fontFamily
                    horizontalPadding: Style.space(4)
                    verticalPadding: Style.spacing.controlPaddingY
                    bordered: true
                    active: root.selectedMonitor && (root.selectedMonitor.transform || 0) === modelData.val

                    onClicked: {
                      if (root.selectedMonitor) {
                        root.setMonitorTransform(root.selectedMonitor.name, modelData.val)
                      }
                    }
                  }
                }
              }
            }

            // 5. Actions: Set Primary & Explicit Power Toggle
            Row {
              width: parent.width
              spacing: Style.space(8)

              Button {
                width: (parent.width - Style.space(8)) / 2
                text: root.selectedMonitor && root.selectedMonitor.is_primary ? "★ Monitor principal" : "Hacer principal (1-9)"
                fontSize: Style.font.caption
                foreground: root.bar.foreground
                fontFamily: root.bar.fontFamily
                bordered: true
                active: root.selectedMonitor && root.selectedMonitor.is_primary
                onClicked: {
                  if (root.selectedMonitor && !root.selectedMonitor.is_primary) {
                    root.setMonitorPrimary(root.selectedMonitor.name)
                  }
                }
              }

              Button {
                width: (parent.width - Style.space(8)) / 2
                text: (root.selectedMonitor && root.selectedMonitor.disabled) ? "Encender pantalla" : "Apagar pantalla"
                fontSize: Style.font.caption
                foreground: (root.selectedMonitor && root.selectedMonitor.disabled) ? Commons.Color.accent : root.bar.foreground
                fontFamily: root.bar.fontFamily
                bordered: true
                // Do not allow turning off if only 1 display is active
                enabled: root.selectedMonitor && (root.selectedMonitor.disabled || root.monitors.filter(m => !m.disabled).length > 1)
                opacity: enabled ? 1.0 : 0.4
                onClicked: {
                  if (root.selectedMonitor) {
                    root.toggleMonitorEnable(root.selectedMonitor.name)
                  }
                }
              }
            }
          }

          // ---------- Night Light ----------
          PanelSeparator {
            foreground: root.bar.foreground
          }

          Column {
            width: parent.width
            spacing: Style.space(6)

            Item {
              width: parent.width
              implicitHeight: Math.max(nightlightHeader.implicitHeight, nightlightToggle.implicitHeight)

              PanelSectionHeader {
                id: nightlightHeader
                text: "Luz nocturna · todas las pantallas"
                foreground: root.bar.foreground
                fontFamily: root.bar.fontFamily
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
              }

              ToggleSwitch {
                id: nightlightToggle
                anchors.right: parent.right
                anchors.rightMargin: Style.space(6)
                anchors.verticalCenter: parent.verticalCenter
                checked: root.nightlightEnabled
                onToggled: function(on) { root.toggleNightlight(on) }
              }
            }

            Item {
              visible: root.nightlightEnabled
              width: parent.width
              implicitHeight: Math.max(nightlightLabel.implicitHeight, nightlightTempText.implicitHeight)

              Text {
                id: nightlightLabel
                text: "Temperatura de color"
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                anchors.left: parent.left
                anchors.leftMargin: Style.space(6)
                anchors.verticalCenter: parent.verticalCenter
              }

              Text {
                id: nightlightTempText
                text: root.nightlightTemp + " K" + (root.nightlightTemp < 4000 ? " (Muy cálido)" : (root.nightlightTemp < 5500 ? " (Cálido)" : " (Neutro)"))
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
                anchors.right: parent.right
                anchors.rightMargin: Style.space(6)
                anchors.verticalCenter: parent.verticalCenter
              }
            }

            CursorSurface {
              id: nightlightRow
              visible: root.nightlightEnabled
              width: parent.width
              height: nightlightSlider.implicitHeight + Style.spacing.controlGap
              foreground: root.bar.foreground
              outline: true

              PanelSlider {
                id: nightlightSlider
                bar: root.bar
                anchors.fill: parent
                anchors.leftMargin: Style.space(6)
                anchors.rightMargin: Style.space(6)
                minimum: 2700
                maximum: 6500
                step: 100
                value: root.nightlightTemp
                integer: true
                onMoved: function(v) { root.nightlightTemp = v }
                onReleased: function(v) { root.setNightlightTemperature(v) }
              }
            }
          }

          // ---------- Text Size (UI Font Base Size) ----------
          PanelSeparator {
            foreground: root.bar.foreground
          }

          Column {
            width: parent.width
            spacing: Style.space(6)

            Item {
              width: parent.width
              implicitHeight: Math.max(textSizeHeader.implicitHeight, textSizePx.implicitHeight)

              PanelSectionHeader {
                id: textSizeHeader
                text: "Tamaño de texto · todas las pantallas"
                foreground: root.bar.foreground
                fontFamily: root.bar.fontFamily
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
              }

              Text {
                id: textSizePx
                textFormat: Text.PlainText
                text: Commons.I18n.formatNumber(textSizeSlider.dragging
                       ? root.textSizeStops[Math.round(textSizeSlider.liveValue)]
                       : root.displayedTextPx()) + "px"
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
                anchors.right: parent.right
                anchors.rightMargin: Style.space(6)
                anchors.verticalCenter: parent.verticalCenter
              }
            }

            CursorSurface {
              id: textSizeRow
              width: parent.width
              height: textSizeSlider.implicitHeight + Style.spacing.controlGap
              foreground: root.bar.foreground
              outline: true

              PanelSlider {
                id: textSizeSlider
                bar: root.bar
                anchors.fill: parent
                anchors.leftMargin: Style.space(6)
                anchors.rightMargin: Style.space(6)
                minimum: 0
                maximum: root.textSizeStops.length - 1
                step: 1
                integer: true
                tickCount: root.textSizeStops.length
                value: root.currentTextIndex()
                onReleased: function(v) { root.setTextSize(root.textSizeStops[Math.round(v)]) }
              }
            }
          }

          Item {
            width: parent.width
            height: Style.space(6)
          }
        }
      }
    }
  }
}
