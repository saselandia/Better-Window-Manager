import QtQuick
import QtQuick.Controls as Controls
import Quickshell
import Quickshell.Wayland
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// BWM: Omarchy's app grid (shell/plugins/dock/AppGrid.qml, MIT), without the dock it
// normally comes with (`dock` stays null: no keep-in-dock).
// Every app on one grid. Type to narrow it, arrows to move, Enter to launch.
Item {
  id: root

  property var appLibrary: null
  property var dock: null
  signal settingsRequested()

  property bool opened: false
  // While an app is dragged out toward the dock, the grid steps aside so the
  // dock shows through, and the app's icon follows the pointer. The grid keeps
  // the pointer for as long as the button is held, and tells the dock where it
  // is.
  property bool dragging: false
  property var dragEntry: null
  property point dragPoint
  // The app waiting on the user to confirm uninstalling it.
  property var uninstallEntry: null
  // The app whose menu is open, and where it opened.
  property var menuEntry: null
  property int menuIndex: 0
  property point menuPoint
  property string filterText: ""
  onFilterTextChanged: if (searchInput.text !== filterText) searchInput.text = filterText
  property int selectedIndex: 0
  property var apps: []

  readonly property int iconSize: Math.round(44 * Style.fontScale)
  readonly property int labelHeight: Math.ceil(labelMetrics.height) * 2
  readonly property int cellGutter: Style.spacing.sm
  readonly property int cellPadding: Style.spacing.lg
  readonly property int cellWidth: Math.round(128 * Style.fontScale)
  readonly property int cellHeight: cellPadding * 2 + iconSize + Style.spacing.md + labelHeight
  readonly property int maxColumns: 6
  readonly property int visibleRows: Math.max(1, Math.min(3, Math.floor((panel.height - screenMargin * 2 - inset * 2 - headerHeight - titleHeight - headerSpacing * 2) / cellHeight)))
  readonly property int titleHeight: Style.space(26)
  readonly property int borderWidth: Math.max(1, Style.space(2))
  readonly property int contentMargin: Style.spacing.panelPadding
  readonly property int inset: contentMargin + borderWidth
  readonly property int headerHeight: Math.max(Style.space(36), Style.font.heading + Style.spacing.controlPaddingY * 2)
  readonly property int headerSpacing: Style.spacing.xl
  readonly property int screenMargin: Style.space(40)

  // The card fits whole columns, and the grid sits centered in it so any
  // leftover width splits evenly on both sides.
  readonly property int cardWidth: Math.min(panel.width - screenMargin * 2, maxColumns * cellWidth + inset * 2)
  readonly property int columns: Math.max(1, Math.floor((cardWidth - inset * 2) / cellWidth))
  readonly property int gridWidth: columns * cellWidth
  readonly property int cardHeight: Math.min(panel.height - screenMargin * 2, inset * 2 + titleHeight + headerHeight + headerSpacing * 2 + visibleRows * cellHeight)

  function inspect() {
    return JSON.stringify({opened: opened, count: apps.length, visible: panel.visible,
      ready: panel.contentRevealed, x: panel.screen ? panel.screen.x + card.x : 0,
      y: panel.screen ? panel.screen.y + card.y : 0, width: card.width, height: card.height})
  }

  function open() {
    root.selectedIndex = 0
    if (root.appLibrary) root.appLibrary.refreshIcons()
    // The cells from last time are reused when nothing changed, so the grid
    // opens with its icons already drawn.
    if (root.appsStale || root.filterText !== "" || root.apps.length === 0) {
      root.filterText = ""
      root.rebuild()
    } else {
      grid.positionViewAtBeginning()
    }
    root.opened = true
    Qt.callLater(function() { searchInput.forceActiveFocus() })
  }

  function close() {
    if (root.dragging && root.dock) root.dock.endExternalDrag()
    root.opened = false
    root.uninstallEntry = null
    root.dragging = false
    root.dragEntry = null
    root.menuEntry = null
  }

  function dragTo(entry, point) {
    if (!root.dragging) {
      root.menuEntry = null
      root.dragEntry = entry
      root.dragging = true
    }
    root.dragPoint = point
    if (root.dock) root.dock.moveExternalDrag(panel.screen, point.x, point.y)
  }

  function dropDrag() {
    var entry = root.dragEntry
    if (entry && root.dock) root.dock.dropExternalDrag(panel.screen, root.dragPoint.x, root.dragPoint.y, String(entry.id || ""))
    root.close()
  }

  function requestUninstall(entry) {
    if (!entry) return
    root.menuEntry = null
    uninstallConfirm.selectedIndex = 1
    root.uninstallEntry = entry
  }

  function cancelUninstall() {
    root.uninstallEntry = null
    Qt.callLater(function() { searchInput.forceActiveFocus() })
  }

  function confirmUninstall() {
    var entry = root.uninstallEntry
    root.uninstallEntry = null
    root.close()
    if (entry && root.appLibrary) root.appLibrary.remove(entry.id, root.appLibrary.entryName(entry))
  }

  function openMenu(entry, point) {
    root.menuEntry = entry
    root.menuIndex = 0
    root.menuPoint = point
  }

  function activateMenu() {
    var entry = root.menuEntry
    if (!entry) return
    if (root.menuIndex === 0) {
      root.close()
      if (root.dock) root.dock.launchEntry(entry)
      else if (root.appLibrary) root.appLibrary.launch(entry.id, root.appLibrary.entryName(entry))
    } else if (root.dock && root.menuIndex === 1) {
      root.dock.setPinned(String(entry.id || ""), !root.dock.isPinned(String(entry.id || "")))
      root.menuEntry = null
    } else root.requestUninstall(entry)
  }

  function toggle() {
    if (root.opened) root.close()
    else root.open()
  }

  function rebuild() {
    root.appsStale = false
    var rows = root.appLibrary ? root.appLibrary.sortedEntries(root.filterText) : []
    root.apps = rows.map(function(row) { return row.entry })
    root.selectedIndex = Math.max(0, Math.min(root.selectedIndex, root.apps.length - 1))
    grid.positionViewAtBeginning()
  }

  function setFilter(text) {
    root.filterText = text
    root.selectedIndex = 0
    root.rebuild()
  }

  function select(delta) {
    if (root.apps.length === 0) return
    root.selectedIndex = Math.max(0, Math.min(root.apps.length - 1, root.selectedIndex + delta))
    grid.positionViewAtIndex(root.selectedIndex, GridView.Contain)
  }

  function launch(index) {
    var entry = root.apps[index]
    if (!entry || !root.appLibrary) return
    root.close()
    if (root.dock) root.dock.launchEntry(entry)
    else root.appLibrary.launch(entry.id, root.appLibrary.entryName(entry))
  }

  FontMetrics {
    id: labelMetrics
    font.family: Style.font.menuFamily
    font.pixelSize: Style.font.body
  }

  // Apps installed or removed while the grid is closed are picked up when it
  // next opens.
  property bool appsStale: false

  Connections {
    target: root.appLibrary
    function onAppsChanged() {
      if (root.opened) root.rebuild()
      else root.appsStale = true
    }
  }

  OverlayWindow {
    id: panel
    shown: root.opened
    WlrLayershell.namespace: "omarchy-dock-apps"
    Rectangle {
      anchors.fill: parent
      color: Commons.Color.menu.scrim
      opacity: root.dragging ? 0 : 1

      Behavior on opacity {
        id: scrimFade
        NumberAnimation { duration: Style.duration(scrimFade.targetValue > 0 ? 150 : 100); easing.type: Easing.OutCubic }
      }
    }

    MouseArea {
      anchors.fill: parent
      acceptedButtons: Qt.LeftButton | Qt.RightButton
      onClicked: {
        if (root.menuEntry) root.menuEntry = null
        else root.close()
      }
    }

    BorderSurface {
      id: card
      width: root.cardWidth
      height: root.cardHeight
      anchors.centerIn: parent
      radius: Style.cornerRadius
      color: Commons.Color.menu.background
      borderSpec: Border.surfaceSpec("menu", "border", Commons.Color.menu.border, root.borderWidth)
      padding: root.contentMargin
      opacity: root.dragging ? 0 : 1

      Behavior on opacity {
        id: cardFade
        NumberAnimation { duration: Style.duration(cardFade.targetValue > 0 ? 150 : 100); easing.type: Easing.OutCubic }
      }

      MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: root.menuEntry = null
      }

      ConfirmDialog {
        id: uninstallConfirm

        anchors.fill: parent
        opened: !!root.uninstallEntry
        z: 10
        message: Commons.I18n.t("common.uninstallConfirm").arg(root.uninstallEntry && root.appLibrary ? root.appLibrary.entryName(root.uninstallEntry) : "")
        confirmText: Commons.I18n.t("common.uninstall")
        background: Commons.Color.menu.background
        foreground: Commons.Color.menu.text
        scrim: Commons.Color.menu.scrim
        selectedBackground: Commons.Color.menu.selectedBackground
        selectedText: Commons.Color.menu.selectedText
        fontFamily: Style.font.menuFamily
        cornerRadius: Style.cornerRadius
        onCanceled: root.cancelUninstall()
        onConfirmed: root.confirmUninstall()
      }

      Item {
        id: keyCatcher
        anchors.fill: parent
        Keys.onPressed: function(event) {
          if (root.uninstallEntry) {
            uninstallConfirm.handleKey(event)
            event.accepted = true
            return
          }
          // Qt owns text, selections, clipboard shortcuts and input-method composition.
          if (searchInput.preeditText.length || searchInput.inputMethodComposing) return
          var control = event.modifiers & Qt.ControlModifier
          var shift = event.modifiers & Qt.ShiftModifier
          if (control && event.key === Qt.Key_Comma) { root.settingsRequested(); event.accepted = true; return }
          if (root.menuEntry) {
            if (event.key === Qt.Key_Escape || event.key === Qt.Key_Left) root.menuEntry = null
            else if (event.key === Qt.Key_Up || event.key === Qt.Key_Backtab) root.menuIndex = Math.max(0, root.menuIndex - 1)
            else if (event.key === Qt.Key_Down || event.key === Qt.Key_Tab) root.menuIndex = Math.min(root.dock ? 2 : 1, root.menuIndex + 1)
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) root.activateMenu()
            else return
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Escape) {
            if (root.menuEntry) root.menuEntry = null
            else if (root.filterText) root.setFilter("")
            else root.close()
          } else if (control && shift && event.key === Qt.Key_Delete) {
            root.requestUninstall(root.apps[root.selectedIndex])
          } else if (event.key === Qt.Key_Menu || (shift && event.key === Qt.Key_F10)) {
            var cell = grid.itemAtIndex(root.selectedIndex)
            if (cell) root.openMenu(root.apps[root.selectedIndex], cell.mapToItem(panel.contentItem, cell.width / 2, cell.height / 2))
          } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
            root.select(event.key === Qt.Key_Backtab || shift ? -1 : 1)
          } else if (!root.filterText && event.modifiers === Qt.NoModifier && event.key === Qt.Key_Left) {
            root.select(-1)
          } else if (!root.filterText && event.modifiers === Qt.NoModifier && event.key === Qt.Key_Right) {
            root.select(1)
          } else if (event.key === Qt.Key_Up) {
            root.select(-root.columns)
          } else if (event.key === Qt.Key_Down) {
            root.select(root.columns)
          } else if (event.key === Qt.Key_PageUp || event.key === Qt.Key_PageDown) {
            root.select((event.key === Qt.Key_PageUp ? -1 : 1) * root.columns * root.visibleRows)
          } else if (!root.filterText && event.key === Qt.Key_Home) {
            root.select(-root.apps.length)
          } else if (!root.filterText && event.key === Qt.Key_End) {
            root.select(root.apps.length)
          } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            root.launch(root.selectedIndex)
          } else {
            return
          }
          event.accepted = true
        }
      }

      Column {
        width: root.gridWidth
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin: card.contentTopInset
        anchors.bottomMargin: card.contentBottomInset
        spacing: root.headerSpacing

        Item {
          width: parent.width
          height: root.titleHeight
          Text {
            anchors.left: parent.left
            anchors.leftMargin: root.cellGutter
            anchors.verticalCenter: parent.verticalCenter
            text: Commons.I18n.t("bwm.apps", Commons.I18n.language.startsWith("es") ? "Aplicaciones" : "Applications")
            color: Commons.Color.menu.text
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.body
          }
          Text {
            anchors.right: settingsButton.left
            anchors.rightMargin: root.cellGutter
            anchors.verticalCenter: parent.verticalCenter
            text: root.apps.length
            color: Commons.Color.menu.text
            opacity: 0.55
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.caption
          }
          Button {
            id: settingsButton
            anchors.right: parent.right
            anchors.rightMargin: root.cellGutter
            anchors.verticalCenter: parent.verticalCenter
            text: "󰒓"
            tooltipText: "Configuración · Ctrl+,"
            focusable: true
            onClicked: root.settingsRequested()
          }
        }

        Rectangle {
          x: root.cellGutter
          width: parent.width - root.cellGutter * 2
          height: root.headerHeight
          radius: Style.cornerRadius
          color: Util.alpha(Commons.Color.menu.text, 0.06)

          border.width: 1
          border.color: searchInput.activeFocus ? Commons.Color.accent : Util.alpha(Commons.Color.menu.text, 0.2)

          TextInput {
            id: searchInput
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: Style.spacing.controlPaddingX
            anchors.rightMargin: Style.spacing.controlPaddingX
            anchors.verticalCenter: parent.verticalCenter
            focus: true
            color: Commons.Color.menu.text
            selectionColor: Commons.Color.menu.selectedBackground
            selectedTextColor: Commons.Color.menu.selectedText
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.heading
            clip: true
            selectByMouse: true
            readOnly: !!root.uninstallEntry
            Keys.priority: Keys.BeforeItem
            Keys.forwardTo: [keyCatcher]
            onTextChanged: if (text !== root.filterText) root.setFilter(text)
          }
          Text {
            anchors.fill: searchInput
            visible: !searchInput.text && !searchInput.preeditText
            text: Commons.I18n.t("dock.searchApps")
            color: Commons.Color.menu.text
            opacity: 0.5
            font: searchInput.font
            elide: Text.ElideRight
          }
        }

        Item {
          width: parent.width
          height: parent.height - root.titleHeight - root.headerHeight - parent.spacing * 2

          GridView {
            id: grid
            anchors.fill: parent
            model: root.apps
            clip: true
            cellWidth: root.cellWidth
            cellHeight: root.cellHeight
            boundsBehavior: Flickable.StopAtBounds
            Controls.ScrollBar.vertical: Controls.ScrollBar {
              policy: Controls.ScrollBar.AsNeeded
              contentItem: Rectangle {
                implicitWidth: Style.space(4)
                color: Util.alpha(Commons.Color.menu.text, 0.4)
                radius: Style.cornerRadius
              }
            }

            delegate: Item {
              id: cell

              required property int index
              required property var modelData
              readonly property bool selected: index === root.selectedIndex
              property point pressPoint
              // A press that wanders is a drag in the making, not a click.
              property bool moved: false

              width: root.cellWidth
              height: root.cellHeight

              Rectangle {
                anchors.fill: parent
                anchors.margins: root.cellGutter / 2
                radius: Style.cornerRadius
                color: cell.selected ? Util.alpha(Commons.Color.accent, 0.1) : "transparent"
                border.width: cell.selected ? 1 : 0
                border.color: Util.alpha(Commons.Color.accent, 0.6)
              }
              Image {
                id: icon
                anchors.horizontalCenter: parent.horizontalCenter
                y: root.cellPadding
                width: root.iconSize
                height: root.iconSize
                sourceSize: Qt.size(root.iconSize * 2, root.iconSize * 2)
                source: root.appLibrary ? root.appLibrary.iconSource(cell.modelData.icon) : ""
                fillMode: Image.PreserveAspectFit
                // Loaded with the cell, from Qt's image cache after the first
                // open, so icons do not pop in after the grid has appeared.
                asynchronous: false
                smooth: true
                mipmap: true
              }

              Text {
                id: label
                anchors.top: icon.bottom
                anchors.topMargin: Style.spacing.md
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width - root.cellGutter * 2
                textFormat: Text.PlainText
                text: root.appLibrary ? root.appLibrary.entryName(cell.modelData) : ""
                color: Commons.Color.menu.text
                font.family: Style.font.menuFamily
                font.pixelSize: Style.font.body
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignTop
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
              }

              MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                // The grid would otherwise take a dragging press for a scroll.
                preventStealing: true
                onPressed: function(event) {
                  cell.moved = false
                  cell.pressPoint = Qt.point(event.x, event.y)
                }
                onPositionChanged: function(event) {
                  if (!pressedButtons && containsMouse && !root.dragging) root.selectedIndex = cell.index
                  if (!(pressedButtons & Qt.LeftButton)) return
                  if (!cell.moved && Math.hypot(event.x - cell.pressPoint.x, event.y - cell.pressPoint.y) > Style.space(4)) cell.moved = true
                  if (cell.moved) root.dragTo(cell.modelData, cell.mapToItem(panel.contentItem, event.x, event.y))
                }
                onReleased: function(event) {
                  if (root.dragging && event.button === Qt.LeftButton) root.dropDrag()
                }
                onCanceled: if (root.dragging) root.close()
                onClicked: function(event) {
                  if (cell.moved) return
                  if (event.button === Qt.RightButton) {
                    root.openMenu(cell.modelData, cell.mapToItem(panel.contentItem, event.x, event.y))
                    return
                  }
                  root.menuEntry = null
                  root.launch(cell.index)
                }
              }
            }
          }

          Text {
            anchors.centerIn: parent
            width: parent.width - Style.spacing.lg * 2
            visible: root.apps.length === 0
            textFormat: Text.PlainText
            text: Commons.I18n.t("dock.noAppsMatch").arg(root.filterText)
            color: Commons.Color.menu.text
            opacity: 0.7
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.title
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            maximumLineCount: 3
            elide: Text.ElideRight
          }
        }

      }
    }
    // The dragged app's icon, under the pointer.
    Image {
      visible: root.dragging && !!root.dragEntry
      x: root.dragPoint.x - width / 2
      y: root.dragPoint.y - height / 2
      width: root.iconSize
      height: root.iconSize
      sourceSize: Qt.size(root.iconSize * 2, root.iconSize * 2)
      source: root.dragEntry && root.appLibrary ? root.appLibrary.iconSource(root.dragEntry.icon) : ""
      fillMode: Image.PreserveAspectFit
      smooth: true
      mipmap: true
    }

    // Right-click on an app: open it, or keep it in the dock or take it out.
    BorderSurface {
      id: menu

      readonly property var entry: root.menuEntry
      readonly property bool pinned: !!entry && !!root.dock && root.dock.isPinned(String(entry.id || ""))

      visible: !!entry && !root.dragging
      width: Math.max(Style.space(160), menuColumn.implicitWidth) + padding * 2
      height: menuColumn.implicitHeight + padding * 2
      // Opens along the reading direction from the pointer.
      x: LayoutMirroring.enabled
        ? Math.max(Style.gapsOut, root.menuPoint.x - width)
        : Math.min(root.menuPoint.x, panel.width - width - Style.gapsOut)
      y: Math.min(root.menuPoint.y, panel.height - height - Style.gapsOut)
      radius: Style.cornerRadius
      color: Commons.Color.popups.background
      borderSpec: Border.surfaceSpec("popups", "border", Commons.Color.popups.border, Style.normalBorderWidth)
      padding: Style.spacing.sm

      Column {
        id: menuColumn
        x: menu.contentLeftInset
        y: menu.contentTopInset
        width: menu.width - menu.contentLeftInset - menu.contentRightInset

        MenuRow {
          menuIndex: 0
          text: Commons.I18n.t("dock.open")
          onTriggered: {
            var entry = menu.entry
            root.close()
            if (entry && root.dock) root.dock.launchEntry(entry)
            else if (entry && root.appLibrary) root.appLibrary.launch(entry.id, root.appLibrary.entryName(entry))
          }
        }

        MenuRow {
          menuIndex: 1
          visible: !!root.dock
          text: menu.pinned ? Commons.I18n.t("dock.removeFromDock") : Commons.I18n.t("dock.keepInDock")
          onTriggered: {
            if (root.dock && menu.entry) root.dock.setPinned(String(menu.entry.id || ""), !menu.pinned)
            root.menuEntry = null
          }
        }

        MenuRow {
          menuIndex: root.dock ? 2 : 1
          text: Commons.I18n.t("dock.uninstall")
          onTriggered: root.requestUninstall(menu.entry)
        }
      }
    }
  }

  component MenuRow: Rectangle {
    id: row

    property string text: ""
    property int menuIndex: 0
    signal triggered()

    width: parent ? parent.width : 0
    height: visible ? Style.spacing.popupRowHeight : 0
    radius: Style.cornerRadius
    color: row.menuIndex === root.menuIndex ? Style.hoverFill : "transparent"

    Text {
      anchors.verticalCenter: parent.verticalCenter
      anchors.left: parent.left
      anchors.leftMargin: Style.spacing.controlPaddingX
      textFormat: Text.PlainText
      text: row.text
      color: Commons.Color.popups.text
      font.family: Style.font.family
      font.pixelSize: Style.font.body
    }

    MouseArea {
      id: rowMouse
      anchors.fill: parent
      hoverEnabled: true
      cursorShape: Qt.PointingHandCursor
      onPositionChanged: if (containsMouse) root.menuIndex = row.menuIndex
      onClicked: row.triggered()
    }
  }
}
