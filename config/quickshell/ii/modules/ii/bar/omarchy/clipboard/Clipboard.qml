import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import qs.Commons
import qs.Commons as Commons
import qs.Ui
import "ClipboardHistory.js" as ClipboardHistory

Item {
  id: root

  property var shell: null
  property var manifest: null

  property bool opened: false
  property string filterText: ""
  property int selectedIndex: 0
  property bool cursorActive: false
  property bool clearConfirmOpen: false
  property var history: []

  property string historyPath: Quickshell.env("HOME") + "/.local/state/omarchy/clipboard-history.json"
  property string captureScript: Qt.resolvedUrl("capture.sh").toString().replace(/^file:\/\//, "")
  // Shares the [menu] surface tokens — themes that style the menu also
  // style the clipboard. Selected-row colors composed in the
  // singleton so consumers drop them straight into Rectangle bindings.
  property color background: Commons.Color.menu.background
  property color foreground: Commons.Color.menu.text
  property color border: Commons.Color.menu.border
  property var borderSpec: Border.surfaceSpec("menu", "border", border, Math.max(1, Style.space(2)))
  property color scrim: Commons.Color.menu.scrim
  property color selectedBackground: Commons.Color.menu.selectedBackground
  property color selectedText: Commons.Color.menu.selectedText
  readonly property int cornerRadius: Style.cornerRadius
  property string fontFamily: Style.font.menuFamily
  property int contentMargin: Style.spacing.panelPadding
  property int headerHeight: Math.max(Style.space(34), Style.font.title + Style.spacing.controlPaddingY * 2)
  property int footerHeight: Style.space(26)
  property int contentSpacing: Style.spacing.sm
  property int cardWidth: Math.min(Style.space(920), panel.width - Style.gapsOut * 2)
  property int cardHeight: Math.min(Style.space(620), panel.height - Style.gapsOut * 2)
  property int rowHeight: Math.max(Style.space(48), Style.font.body + Style.font.caption + Style.spacing.rowPaddingX * 2)
  property int historyLimit: 500

  readonly property var activeRow: displayModel.count > 0 && selectedIndex >= 0 && selectedIndex < displayModel.count
    ? displayModel.get(selectedIndex)
    : null

  function open(payloadJson) {
    root.opened = true
    root.filterText = ""
    root.selectedIndex = 0
    root.cursorActive = true
    root.disarmPointer()
    root.rebuildDisplay()
    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }

  function close() {
    root.cancelClearHistory()
    root.opened = false
  }

  function dismiss() {
    root.close()
    if (root.shell && typeof root.shell.hide === "function")
      root.shell.hide((root.manifest && root.manifest.id) || "omarchy.clipboard")
  }

  function toggle() {
    if (root.opened) root.dismiss()
    else root.open("{}")
  }

  function normalizeEntry(value) {
    return ClipboardHistory.normalizeEntry(value)
  }

  function entryKey(entry) {
    return ClipboardHistory.entryKey(entry)
  }

  function loadHistory(raw) {
    root.history = ClipboardHistory.parseHistory(raw)
    if (root.opened) root.rebuildDisplay()
  }

  function saveHistory() {
    historyFile.setText(JSON.stringify(root.history.slice(0, root.historyLimit), null, 2) + "\n")
  }

  function addClipboardEntry(entry) {
    var normalized = ClipboardHistory.normalizeEntry(entry)
    if (!normalized) return

    root.history = ClipboardHistory.addEntry(root.history, normalized, root.historyLimit)
    root.saveHistory()
    if (root.opened) root.rebuildDisplay()
  }

  function addClipboardJson(line) {
    root.addClipboardEntry(ClipboardHistory.parseEntryJson(line))
  }

  function requestClearHistory() {
    if (root.history.length === 0) return
    clearConfirm.selectedIndex = 1
    root.clearConfirmOpen = true
  }

  function cancelClearHistory() {
    root.clearConfirmOpen = false
    root.disarmPointer()
    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }

  function confirmClearHistory() {
    root.history = ClipboardHistory.clearHistory()
    root.saveHistory()
    root.selectedIndex = 0
    root.cursorActive = false
    root.disarmPointer()
    root.clearConfirmOpen = false
    root.rebuildDisplay()
    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }

  function removeDisplayIndex(index) {
    if (index < 0 || index >= displayModel.count) return

    var row = displayModel.get(index)
    root.history = ClipboardHistory.removeEntryAt(root.history, row.historyIndex)
    root.saveHistory()

    if (displayModel.count <= 1) {
      root.selectedIndex = 0
      root.cursorActive = false
    } else if (root.selectedIndex >= displayModel.count - 1) {
      root.selectedIndex = displayModel.count - 2
    }

    root.disarmPointer()
    root.rebuildDisplay()
  }

  function rebuildDisplay() {
    var rows = ClipboardHistory.displayRows(root.history, root.filterText, 100, Commons.I18n.t, Commons.I18n.tn, Commons.I18n.formatNumber)

    displayModel.clear()
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i]
      displayModel.append({
        entryType: row.entryType,
        fullText: row.fullText,
        previewText: row.previewText,
        previewImage: row.previewImage ? Util.fileUrl(row.previewImage) : "",
        colorHex: row.colorHex || "",
        lineCount: row.lineCount || 1,
        charCount: row.charCount || 0,
        capturedAt: row.capturedAt || "",
        path: row.path,
        mime: row.mime,
        historyIndex: row.index
      })
    }

    if (displayModel.count === 0) selectedIndex = 0
    else if (selectedIndex >= displayModel.count) selectedIndex = displayModel.count - 1
    else if (selectedIndex < 0) selectedIndex = 0

    Qt.callLater(function() {
      if (displayModel.count > 0) resultList.positionViewAtIndex(root.selectedIndex, ListView.Contain)
    })
  }

  // Preview text is composed imperatively, so rebuild it when the
  // language (and with it the string catalog) changes under an open panel.
  Connections {
    target: Commons.I18n
    function onStringsChanged() { if (root.opened) root.rebuildDisplay() }
  }

  function select(delta) {
    if (displayModel.count === 0) return
    root.disarmPointer()
    if (!cursorActive) {
      cursorActive = true
      selectedIndex = delta < 0 ? displayModel.count - 1 : 0
    } else {
      selectedIndex = (selectedIndex + delta + displayModel.count) % displayModel.count
    }
    resultList.positionViewAtIndex(selectedIndex, ListView.Contain)
  }

  function selectAbsolute(index) {
    if (displayModel.count === 0) return
    root.disarmPointer()
    root.cursorActive = true
    root.selectedIndex = Math.max(0, Math.min(index, displayModel.count - 1))
    resultList.positionViewAtIndex(root.selectedIndex, ListView.Contain)
  }

  function setFilter(nextFilter) {
    root.filterText = nextFilter
    root.selectedIndex = 0
    root.cursorActive = true
    root.disarmPointer()
    root.rebuildDisplay()
  }

  function disarmPointer() {
    pointerGate.reset()
  }

  function selectFromPointer(index, item, mouse) {
    if (!pointerGate.moved(item, mouse)) return
    root.cursorActive = true
    root.selectedIndex = index
  }

  function activateIndex(index) {
    if (index < 0 || index >= displayModel.count) return
    var row = displayModel.get(index)
    root.applySelected(row)
  }

  function copyIndex(index) {
    if (index < 0 || index >= displayModel.count) return
    var row = displayModel.get(index)
    root.copySelected(row)
  }

  function openIndex(index) {
    if (index < 0 || index >= displayModel.count) return
    var row = displayModel.get(index)
    root.openSelected(row)
  }

  function applySelected(row) {
    if (!row) return
    root.opened = false
    if (row.entryType === "image") {
      Quickshell.execDetached(["omarchy-clipboard-paste-file", row.mime, row.path])
    } else if (row.fullText) {
      Quickshell.execDetached(["omarchy-clipboard-paste-text", "--shift-insert", "--history-index", String(row.historyIndex)])
    }
  }

  function copySelected(row) {
    if (!row) return
    root.opened = false
    if (row.entryType === "image") {
      Quickshell.execDetached(["omarchy-clipboard-paste-file", "--copy-only", row.mime, row.path])
    } else if (row.fullText) {
      Quickshell.execDetached(["omarchy-clipboard-paste-text", "--copy-only", "--history-index", String(row.historyIndex)])
    }
  }

  function openSelected(row) {
    if (!row) return
    root.opened = false
    Quickshell.execDetached(["omarchy-clipboard-open", "--history-index", String(row.historyIndex)])
  }

  Component.onCompleted: initProc.running = true

  ListModel { id: displayModel }

  PointerMoveGate {
    id: pointerGate
    referenceItem: card
  }

  FileView {
    id: historyFile
    path: root.historyPath
    watchChanges: true
    atomicWrites: true
    printErrors: false
    onLoaded: root.loadHistory(text())
    onLoadFailed: root.loadHistory("[]")
    onFileChanged: reload()
  }

  // Reap watchers left behind by a previous shell instance, then start our
  // own. Clean process termination handles the watchers.
  Process {
    id: initProc
    command: ["pkill", "-f", "wl-paste .*--watch .*clipboard/capture\\.sh"]
    onExited: {
      currentProc.running = true
      textWatchProc.running = true
      imageWatchProc.running = true
    }
  }

  Process {
    id: currentProc
    command: [root.captureScript]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.addClipboardJson(text)
    }
  }

  Process {
    id: textWatchProc
    command: ["wl-paste", "--type", "text", "--watch", root.captureScript, "text"]
    onExited: watchRestartTimer.restart()
    stdout: SplitParser {
      onRead: function(data) { root.addClipboardJson(data) }
    }
  }

  Process {
    id: imageWatchProc
    command: ["wl-paste", "--type", "image/png", "--watch", root.captureScript, "image/png"]
    onExited: watchRestartTimer.restart()
    stdout: SplitParser {
      onRead: function(data) { root.addClipboardJson(data) }
    }
  }

  Timer {
    id: watchRestartTimer
    interval: 1000
    repeat: false
    onTriggered: {
      if (!textWatchProc.running) textWatchProc.running = true
      if (!imageWatchProc.running) imageWatchProc.running = true
    }
  }

  OverlayWindow {
    id: panel
    shown: root.opened
    WlrLayershell.namespace: "omarchy-clipboard"

    Rectangle {
      anchors.fill: parent
      color: root.scrim
    }

    MouseArea {
      anchors.fill: parent
      onClicked: root.dismiss()
    }

    BorderSurface {
      id: card
      width: root.cardWidth
      height: root.cardHeight
      radius: root.cornerRadius
      anchors.centerIn: parent
      color: root.background
      borderSpec: root.borderSpec
      padding: root.contentMargin

      MouseArea { anchors.fill: parent; onClicked: {} }

      Item {
        id: keyCatcher
        anchors.fill: parent
        z: root.clearConfirmOpen ? 20 : 0
        focus: true

        Keys.priority: Keys.BeforeItem
        Keys.onPressed: function(event) {
          if (root.clearConfirmOpen) {
            if (clearConfirm.handleKey(event)) event.accepted = true
            return
          }

          if (event.key === Qt.Key_Escape) {
            if (root.filterText) root.setFilter("")
            else root.dismiss()
            event.accepted = true
          } else if ((event.modifiers & Qt.ControlModifier) && (event.key === Qt.Key_Backspace || event.key === Qt.Key_W)) {
            var words = root.filterText.trim().split(/\s+/)
            if (words.length > 1) {
              words.pop()
              root.setFilter(words.join(" "))
            } else {
              root.setFilter("")
            }
            event.accepted = true
          } else if (Util.editsFilter(event, root.filterText)) {
            root.setFilter(Util.editedFilter(event, root.filterText))
            event.accepted = true
          } else if ((event.modifiers & Qt.ControlModifier) && (event.key === Qt.Key_C || event.key === Qt.Key_Insert)) {
            if (root.cursorActive) root.copyIndex(root.selectedIndex)
            event.accepted = true
          } else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_V) {
            if (root.cursorActive) root.activateIndex(root.selectedIndex)
            event.accepted = true
          } else if (event.key === Qt.Key_Tab || ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_N)) {
            root.select(1)
            event.accepted = true
          } else if (event.key === Qt.Key_Backtab || ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_P)) {
            root.select(-1)
            event.accepted = true
          } else if (event.key === Qt.Key_Delete) {
            if (event.modifiers & Qt.ShiftModifier) root.requestClearHistory()
            else root.removeDisplayIndex(root.selectedIndex)
            event.accepted = true
          } else if (event.key === Qt.Key_Up) {
            root.select(-1)
            event.accepted = true
          } else if (event.key === Qt.Key_Down) {
            root.select(1)
            event.accepted = true
          } else if (event.key === Qt.Key_PageUp) {
            root.select(-6)
            event.accepted = true
          } else if (event.key === Qt.Key_PageDown) {
            root.select(6)
            event.accepted = true
          } else if (event.key === Qt.Key_Home) {
            root.selectAbsolute(0)
            event.accepted = true
          } else if (event.key === Qt.Key_End) {
            root.selectAbsolute(displayModel.count - 1)
            event.accepted = true
          } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            if (root.cursorActive && (event.modifiers & Qt.AltModifier)) root.openIndex(root.selectedIndex)
            else if (root.cursorActive && (event.modifiers & Qt.ShiftModifier)) root.copyIndex(root.selectedIndex)
            else if (root.cursorActive) root.activateIndex(root.selectedIndex)
            else if (displayModel.count > 0) root.cursorActive = true
            event.accepted = true
          } else if (event.text && event.text.length === 1 && event.text.charCodeAt(0) >= 32 && event.text.charCodeAt(0) !== 127) {
            root.setFilter(root.filterText + event.text)
            event.accepted = true
          }
        }

        ConfirmDialog {
          id: clearConfirm

          anchors.fill: parent
          opened: root.clearConfirmOpen
          z: 10
          message: Commons.I18n.t("clipboard.deleteHistory")
          confirmText: Commons.I18n.t("common.delete")
          background: root.background
          foreground: root.foreground
          scrim: root.scrim
          selectedBackground: root.selectedBackground
          selectedText: root.selectedText
          fontFamily: root.fontFamily
          cornerRadius: root.cornerRadius
          onCanceled: root.cancelClearHistory()
          onConfirmed: root.confirmClearHistory()
        }
      }

      Column {
        anchors.fill: parent
        anchors.topMargin: card.contentTopInset
        anchors.rightMargin: card.contentRightInset
        anchors.bottomMargin: card.contentBottomInset
        anchors.leftMargin: card.contentLeftInset
        spacing: root.contentSpacing

        // Search Header
        Item {
          width: parent.width
          height: root.headerHeight

          Row {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            spacing: Style.space(8)

            Text {
              anchors.verticalCenter: parent.verticalCenter
              text: "󰍉"
              color: root.selectedText
              font.family: root.fontFamily
              font.pixelSize: Style.font.heading
            }

            Text {
              textFormat: Text.PlainText
              width: parent.parent.width - Style.space(120)
              anchors.verticalCenter: parent.verticalCenter
              text: root.filterText || Commons.I18n.t("clipboard.search")
              color: root.foreground
              opacity: root.filterText ? 1 : 0.58
              font.family: root.fontFamily
              font.pixelSize: Style.font.heading
              elide: Text.ElideRight
            }
          }

          Text {
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            text: displayModel.count + " / " + root.history.length
            color: root.foreground
            opacity: 0.45
            font.family: root.fontFamily
            font.pixelSize: Style.font.caption
          }
        }

        Rectangle {
          width: parent.width
          height: 1
          color: Util.alpha(root.border, 0.25)
        }

        // Main Body: Split List & Rich Preview
        Item {
          width: parent.width
          height: parent.height - root.headerHeight - root.footerHeight - root.contentSpacing * 3 - 2

          Row {
            anchors.fill: parent
            spacing: 0

            // Left: History List
            Item {
              width: parent.width * 0.52
              height: parent.height
              clip: true

              ListView {
                id: resultList
                anchors.fill: parent
                anchors.rightMargin: Style.space(8)
                model: displayModel
                clip: true
                spacing: Style.space(3)
                boundsBehavior: Flickable.StopAtBounds

                delegate: Rectangle {
                  id: row
                  required property int index
                  required property string entryType
                  required property string previewText
                  required property string fullText
                  required property string previewImage
                  required property string colorHex
                  required property int lineCount
                  required property int charCount

                  readonly property bool hasCursor: root.cursorActive && index === root.selectedIndex

                  width: ListView.view.width
                  height: root.rowHeight
                  radius: root.cornerRadius
                  color: hasCursor ? root.selectedBackground : "transparent"

                  Row {
                    anchors.fill: parent
                    anchors.leftMargin: Style.space(10)
                    anchors.rightMargin: Style.space(10)
                    anchors.topMargin: Style.space(6)
                    anchors.bottomMargin: Style.space(6)
                    spacing: Style.space(10)

                    // Image Thumbnail
                    Rectangle {
                      visible: parent.parent.previewImage.length > 0
                      width: visible ? parent.height : 0
                      height: parent.height
                      radius: Style.space(4)
                      color: "transparent"
                      clip: true

                      SizedImage {
                        anchors.fill: parent
                        url: parent.parent.parent.previewImage
                        asynchronous: true
                        smooth: true
                      }
                    }

                    // Color Swatch Chip
                    Rectangle {
                      visible: parent.parent.entryType === "color" && parent.parent.previewImage.length === 0
                      width: visible ? parent.height * 0.75 : 0
                      height: parent.height * 0.75
                      anchors.verticalCenter: parent.verticalCenter
                      radius: Style.space(4)
                      color: parent.parent.colorHex || "transparent"
                      border.width: 1
                      border.color: Util.alpha(root.foreground, 0.25)
                    }

                    // Type Icon (for URL, File, Text)
                    Text {
                      visible: parent.parent.previewImage.length === 0 && parent.parent.entryType !== "color"
                      anchors.verticalCenter: parent.verticalCenter
                      text: parent.parent.entryType === "url" ? "󰌹" : (parent.parent.entryType === "file" ? "󰈔" : "󰦨")
                      color: parent.parent.hasCursor ? root.selectedText : Util.alpha(root.foreground, 0.6)
                      font.family: root.fontFamily
                      font.pixelSize: Style.font.title
                    }

                    // Text Content
                    Text {
                      textFormat: Text.PlainText
                      width: parent.width - (parent.parent.previewImage.length > 0 ? parent.height + parent.spacing : (parent.parent.entryType === "color" ? parent.height * 0.75 + parent.spacing : Style.space(24))) - (parent.parent.lineCount > 1 ? Style.space(45) : 0)
                      height: parent.height
                      text: parent.parent.previewText
                      color: parent.parent.hasCursor ? root.selectedText : root.foreground
                      font.family: root.fontFamily
                      font.pixelSize: Style.font.body
                      opacity: parent.parent.entryType === "image" || parent.parent.entryType === "file" ? 0.75 : 1.0
                      elide: Text.ElideRight
                      wrapMode: Text.NoWrap
                      verticalAlignment: Text.AlignVCenter
                    }

                    // Multiline line count tag
                    Text {
                      visible: parent.parent.lineCount > 1
                      anchors.verticalCenter: parent.verticalCenter
                      text: parent.parent.lineCount + " l."
                      color: parent.parent.hasCursor ? root.selectedText : root.foreground
                      opacity: 0.45
                      font.family: root.fontFamily
                      font.pixelSize: Style.font.caption
                    }
                  }

                  MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPositionChanged: function(mouse) {
                      root.selectFromPointer(row.index, row, mouse)
                    }
                    onClicked: {
                      root.cursorActive = true
                      root.selectedIndex = row.index
                      root.activateIndex(row.index)
                    }
                  }
                }
              }
            }

            // Right: Rich Detail Preview Panel
            Item {
              width: parent.width * 0.48
              height: parent.height
              clip: true

              Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: Style.normalBorderWidth
                color: Util.alpha(root.border, 0.28)
              }

              Column {
                anchors.fill: parent
                anchors.leftMargin: root.contentMargin
                spacing: Style.space(10)
                visible: root.activeRow !== null

                // Preview Type Header
                Item {
                  width: parent.width
                  height: Style.space(22)

                  Row {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Style.space(8)

                    Text {
                      text: root.activeRow ? (
                        root.activeRow.entryType === "color" ? "󰏘" :
                        root.activeRow.entryType === "url" ? "󰖟" :
                        root.activeRow.entryType === "image" ? "󰋩" :
                        root.activeRow.entryType === "file" ? "󰈔" : "󰦨"
                      ) : ""
                      color: root.selectedText
                      font.family: root.fontFamily
                      font.pixelSize: Style.font.body
                    }

                    Text {
                      text: root.activeRow ? (
                        root.activeRow.entryType === "color" ? "Color HEX" :
                        root.activeRow.entryType === "url" ? "Enlace Web" :
                        root.activeRow.entryType === "image" ? "Imagen" :
                        root.activeRow.entryType === "file" ? "Archivo" : "Texto"
                      ) : ""
                      color: root.foreground
                      font.family: root.fontFamily
                      font.bold: true
                      font.pixelSize: Style.font.body
                    }
                  }

                  Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.activeRow ? (
                      root.activeRow.entryType === "image" ? (root.activeRow.capturedAt || "Captura") :
                      (root.activeRow.lineCount + " l. • " + root.activeRow.charCount + " c.")
                    ) : ""
                    color: root.foreground
                    opacity: 0.5
                    font.family: root.fontFamily
                    font.pixelSize: Style.font.caption
                  }
                }

                Rectangle {
                  width: parent.width
                  height: 1
                  color: Util.alpha(root.border, 0.2)
                }

                // Color View
                Column {
                  visible: root.activeRow && root.activeRow.entryType === "color"
                  width: parent.width
                  spacing: Style.space(12)

                  Rectangle {
                    width: parent.width
                    height: Style.space(110)
                    radius: root.cornerRadius
                    color: (root.activeRow && root.activeRow.colorHex) || "transparent"
                    border.width: 1
                    border.color: Util.alpha(root.foreground, 0.2)
                  }

                  Text {
                    text: (root.activeRow && root.activeRow.colorHex) || ""
                    color: root.foreground
                    font.family: root.fontFamily
                    font.bold: true
                    font.pixelSize: Style.font.heading
                  }

                  Text {
                    text: "Color detectado en el portapapeles. Pulsa Enter para pegar o Shift+Enter para copiar."
                    color: root.foreground
                    opacity: 0.65
                    font.family: root.fontFamily
                    font.pixelSize: Style.font.caption
                    wrapMode: Text.Wrap
                    width: parent.width
                  }
                }

                // Image View
                Item {
                  visible: root.activeRow && root.activeRow.entryType === "image"
                  width: parent.width
                  height: parent.height - Style.space(70)

                  SizedImage {
                    anchors.fill: parent
                    url: root.activeRow ? root.activeRow.previewImage : ""
                    verticalAlignment: Image.AlignTop
                    asynchronous: true
                    smooth: true
                  }
                }

                // URL View
                Column {
                  visible: root.activeRow && root.activeRow.entryType === "url"
                  width: parent.width
                  spacing: Style.space(8)

                  Text {
                    text: (root.activeRow && root.activeRow.fullText) || ""
                    color: root.selectedText
                    font.family: root.fontFamily
                    font.pixelSize: Style.font.body
                    font.underline: true
                    wrapMode: Text.WrapAnywhere
                    width: parent.width
                  }

                  Text {
                    text: "Pulsa Alt+Enter para abrir en tu navegador web predeterminado."
                    color: root.foreground
                    opacity: 0.65
                    font.family: root.fontFamily
                    font.pixelSize: Style.font.caption
                  }
                }

                // Text / File View (Scrollable / Monospace)
                Item {
                  visible: root.activeRow && root.activeRow.entryType !== "image" && root.activeRow.entryType !== "color" && root.activeRow.entryType !== "url"
                  width: parent.width
                  height: parent.height - Style.space(40)

                  Flickable {
                    anchors.fill: parent
                    contentWidth: width
                    contentHeight: fullTextPreview.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    Text {
                      id: fullTextPreview
                      width: parent.width
                      textFormat: Text.PlainText
                      text: root.activeRow ? root.activeRow.fullText : ""
                      color: root.foreground
                      font.family: Style.font.codeFamily || "monospace"
                      font.pixelSize: Style.font.body
                      wrapMode: Text.WrapAnywhere
                      verticalAlignment: Text.AlignTop
                    }
                  }
                }
              }
            }
          }

          Column {
            anchors.centerIn: parent
            spacing: Style.space(8)
            visible: displayModel.count === 0

            Text {
              text: "󰅌"
              color: root.selectedText
              opacity: 0.8
              font.family: root.fontFamily
              font.pixelSize: Style.font.displayLarge
              horizontalAlignment: Text.AlignHCenter
              width: parent.width
            }

            Text {
              textFormat: Text.PlainText
              text: root.history.length === 0 ? Commons.I18n.t("clipboard.empty") : Commons.I18n.t("common.noMatchesFor").arg(root.filterText)
              color: root.foreground
              opacity: 0.7
              font.family: root.fontFamily
              font.pixelSize: Style.font.title
              horizontalAlignment: Text.AlignHCenter
              width: parent.width
            }
          }
        }

        Rectangle {
          width: parent.width
          height: 1
          color: Util.alpha(root.border, 0.25)
        }

        // Footer Cheatsheet
        Row {
          width: parent.width
          height: root.footerHeight
          spacing: Style.space(16)

          Row {
            spacing: Style.space(4)
            Text { text: "↵"; font.bold: true; color: root.selectedText; font.pixelSize: Style.font.caption }
            Text { text: "Pegar"; color: root.foreground; opacity: 0.75; font.pixelSize: Style.font.caption }
          }
          Row {
            spacing: Style.space(4)
            Text { text: "⇧↵ / Ctrl+C"; font.bold: true; color: root.selectedText; font.pixelSize: Style.font.caption }
            Text { text: "Copiar"; color: root.foreground; opacity: 0.75; font.pixelSize: Style.font.caption }
          }
          Row {
            spacing: Style.space(4)
            Text { text: "⎇↵"; font.bold: true; color: root.selectedText; font.pixelSize: Style.font.caption }
            Text { text: "Abrir"; color: root.foreground; opacity: 0.75; font.pixelSize: Style.font.caption }
          }
          Row {
            spacing: Style.space(4)
            Text { text: "Supr"; font.bold: true; color: root.selectedText; font.pixelSize: Style.font.caption }
            Text { text: "Borrar"; color: root.foreground; opacity: 0.75; font.pixelSize: Style.font.caption }
          }
          Row {
            spacing: Style.space(4)
            Text { text: "⇧Supr"; font.bold: true; color: root.selectedText; font.pixelSize: Style.font.caption }
            Text { text: "Vaciar"; color: root.foreground; opacity: 0.75; font.pixelSize: Style.font.caption }
          }
          Row {
            spacing: Style.space(4)
            Text { text: "Esc"; font.bold: true; color: root.selectedText; font.pixelSize: Style.font.caption }
            Text { text: "Cerrar"; color: root.foreground; opacity: 0.75; font.pixelSize: Style.font.caption }
          }
        }
      }
    }
  }
}
