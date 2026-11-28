// SPDX-FileCopyrightText: 2021 Vlad Zahorodnii <vlad.zahorodnii@kde.org>
// SPDX-FileCopyrightText: 2026 BWM contributors
// SPDX-License-Identifier: GPL-2.0-or-later
// Adapted from KWin 6.7.5 overview/windowview/WindowHeapDelegate QML to run
// inside bwm-plasma-host over LayerShellQt with live Hyprland screencopy
// thumbnails (bwmScreenshareMonitorGuard) and org.kde.milou KRunner search.

import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.milou as Milou
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import org.bwm.kwin.effects 1.0 as KWinEffects

Item {
    id: root
    focus: true

    readonly property string currentMode: overviewHost ? overviewHost.mode : "overview"
    readonly property bool isOverview: currentMode === "overview"
    readonly property bool isGrid: currentMode === "grid"
    readonly property bool isWindowView: currentMode === "windowview" || currentMode === "windowview-all"
    readonly property bool showAllWorkspaces: currentMode === "windowview-all"
    readonly property int activeWsId: overviewHost ? overviewHost.activeWorkspaceId : 1
    readonly property bool magicOpen: overviewHost ? overviewHost.magicOpen : false

    property real activationFactor: 0.0
    property string draggedAddress: ""

    Component.onCompleted: {
        activationFactor = 1.0;
        if (isPrimaryOverviewScreen && searchField.visible) {
            searchField.forceActiveFocus();
        }
    }

    Behavior on activationFactor {
        NumberAnimation {
            duration: Kirigami.Units.longDuration
            easing.type: Easing.OutCubic
        }
    }

    // Scrim backdrop with KWin-like opacity ramp
    Rectangle {
        anchors.fill: parent
        color: Kirigami.Theme.backgroundColor
        opacity: (isGrid ? 0.82 : 0.72) * root.activationFactor
    }

    // Clicking empty background closes the overview (matches KWin)
    MouseArea {
        anchors.fill: parent
        onClicked: overviewHost.close()
    }

    // Reusable window card matching KWin 6.7.5 WindowHeapDelegate
    Component {
        id: windowCardComponent
        Item {
            id: wrapper
            required property var modelData
            required property var targetLayout
            required property bool compactMode
            required property bool showWorkspaceBadge
            anchors.fill: parent

            KWinEffects.ExpoCell {
                id: cell
                layout: wrapper.targetLayout
                contentItem: card
                naturalX: wrapper.modelData.x ?? 0
                naturalY: wrapper.modelData.y ?? 0
                naturalWidth: Math.max(120, wrapper.modelData.width ?? 640)
                naturalHeight: Math.max(90, wrapper.modelData.height ?? 420)
                partialActivationFactor: root.activationFactor
                persistentKey: wrapper.modelData.address ?? ""
                bottomMargin: wrapper.compactMode ? 6 : 26
            }

            Item {
                id: card
                scale: hoverHandler.hovered && !dragHandler.active ? 1.02 : 1.0
                z: dragHandler.active ? 100 : (hoverHandler.hovered ? 10 : 1)

                Behavior on scale {
                    NumberAnimation { duration: Kirigami.Units.shortDuration; easing.type: Easing.OutCubic }
                }

                Drag.active: dragHandler.active
                Drag.hotSpot.x: width / 2
                Drag.hotSpot.y: height / 2
                Drag.mimeData: ({ "text/x-bwm-window-address": wrapper.modelData.address ?? "" })

                Rectangle {
                    anchors.fill: parent
                    radius: Kirigami.Units.cornerRadius * 1.5
                    color: Qt.rgba(Kirigami.Theme.backgroundColor.r,
                                   Kirigami.Theme.backgroundColor.g,
                                   Kirigami.Theme.backgroundColor.b, 0.92)
                    border.width: hoverHandler.hovered ? 2 : 1
                    border.color: hoverHandler.hovered
                        ? Kirigami.Theme.highlightColor
                        : Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.22)
                    clip: true

                    // Live screencopy thumbnail (guarded by bwmScreenshareMonitorGuard)
                    KWinEffects.WindowThumbnail {
                        id: liveThumb
                        anchors.fill: parent
                        anchors.margins: 2
                        uuid: (!wrapper.modelData.minimized && wrapper.modelData.uuid) ? wrapper.modelData.uuid : ""
                        visible: uuid.length > 0
                    }

                    // Fallback icon & title when thumbnail is unavailable or minimized
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: Kirigami.Units.smallSpacing
                        visible: !liveThumb.ready
                        Kirigami.Icon {
                            Layout.alignment: Qt.AlignHCenter
                            implicitWidth: Math.min(64, Math.max(24, card.height * 0.35))
                            implicitHeight: implicitWidth
                            source: modelData.iconName || "window"
                        }
                        PC3.Label {
                            visible: !compactMode
                            Layout.alignment: Qt.AlignHCenter
                            Layout.maximumWidth: Math.max(60, card.width - 24)
                            text: modelData.appClass || ""
                            elide: Text.ElideRight
                            opacity: 0.75
                        }
                    }

                    // Workspace / Magic / Minimized badge
                    Rectangle {
                        visible: showWorkspaceBadge || modelData.minimized || modelData.magic
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.margins: Kirigami.Units.smallSpacing
                        radius: Kirigami.Units.cornerRadius
                        color: modelData.magic ? Kirigami.Theme.highlightColor
                             : Qt.rgba(Kirigami.Theme.backgroundColor.r, Kirigami.Theme.backgroundColor.g, Kirigami.Theme.backgroundColor.b, 0.85)
                        implicitWidth: badgeLabel.implicitWidth + 12
                        implicitHeight: badgeLabel.implicitHeight + 4
                        PC3.Label {
                            id: badgeLabel
                            anchors.centerIn: parent
                            font.pointSize: Math.max(8, Kirigami.Theme.smallFont.pointSize)
                            text: modelData.magic ? "Magic"
                                : (modelData.minimized ? i18nd("kwin", "Minimized")
                                   : i18nd("kwin", "Desktop %1", modelData.workspaceId))
                        }
                    }

                    // Hover close button (KWin WindowHeapDelegate style)
                    PC3.Button {
                        visible: !compactMode && hoverHandler.hovered && !dragHandler.active
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: Kirigami.Units.smallSpacing
                        icon.name: "window-close"
                        display: PC3.AbstractButton.IconOnly
                        flat: false
                        onClicked: overviewHost.closeWindow(modelData.address)
                    }
                }

                // Bottom caption pill (KWin WindowHeapDelegate style)
                Rectangle {
                    visible: !compactMode
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.bottom
                    anchors.topMargin: 4
                    radius: height / 2
                    color: hoverHandler.hovered
                        ? Kirigami.Theme.highlightColor
                        : Qt.rgba(Kirigami.Theme.backgroundColor.r, Kirigami.Theme.backgroundColor.g, Kirigami.Theme.backgroundColor.b, 0.85)
                    implicitHeight: Math.max(22, captionRow.implicitHeight + 4)
                    implicitWidth: Math.min(card.width, captionRow.implicitWidth + 16)

                    RowLayout {
                        id: captionRow
                        anchors.centerIn: parent
                        spacing: 6
                        Kirigami.Icon {
                            implicitWidth: 16
                            implicitHeight: 16
                            source: modelData.iconName || "window"
                        }
                        PC3.Label {
                            Layout.maximumWidth: Math.max(40, card.width - 44)
                            text: modelData.title || modelData.appClass || ""
                            elide: Text.ElideRight
                            color: hoverHandler.hovered ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                        }
                    }
                }

                HoverHandler { id: hoverHandler }

                DragHandler {
                    id: dragHandler
                    target: card
                    onActiveChanged: {
                        if (active) {
                            root.draggedAddress = wrapper.modelData.address ?? "";
                        } else {
                            card.Drag.drop();
                            root.draggedAddress = "";
                            card.x = cell.x;
                            card.y = cell.y;
                        }
                    }
                }

                TapHandler {
                    onTapped: {
                        overviewHost.activateWindow(
                            modelData.address ?? "",
                            modelData.workspaceId ?? 1,
                            modelData.minimized ?? false,
                            modelData.special ?? false
                        );
                    }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing * 2
        spacing: Kirigami.Units.largeSpacing

        // Top DesktopBar (Overview mode)
        Rectangle {
            id: desktopBar
            visible: root.isOverview
            Layout.fillWidth: true
            Layout.preferredHeight: 84
            radius: Kirigami.Units.cornerRadius * 2
            color: Qt.rgba(Kirigami.Theme.backgroundColor.r,
                           Kirigami.Theme.backgroundColor.g,
                           Kirigami.Theme.backgroundColor.b, 0.65)
            border.width: 1
            border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.14)

            RowLayout {
                anchors.centerIn: parent
                spacing: Kirigami.Units.largeSpacing

                Repeater {
                    model: overviewHost ? overviewHost.workspaces : []
                    delegate: Item {
                        required property var modelData
                        implicitWidth: 120
                        implicitHeight: 64

                        Rectangle {
                            id: wsThumb
                            anchors.fill: parent
                            radius: Kirigami.Units.cornerRadius * 1.5
                            color: wsDrop.containsDrag
                                ? Kirigami.Theme.highlightColor
                                : (modelData.active
                                    ? Qt.rgba(Kirigami.Theme.highlightColor.r, Kirigami.Theme.highlightColor.g, Kirigami.Theme.highlightColor.b, 0.35)
                                    : Qt.rgba(Kirigami.Theme.backgroundColor.r, Kirigami.Theme.backgroundColor.g, Kirigami.Theme.backgroundColor.b, 0.8))
                            border.width: modelData.active || wsDrop.containsDrag ? 2 : 1
                            border.color: modelData.active || wsDrop.containsDrag
                                ? Kirigami.Theme.highlightColor
                                : Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.25)

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 2
                                PC3.Label {
                                    Layout.alignment: Qt.AlignHCenter
                                    font.bold: modelData.active
                                    text: i18nd("kwin", "Desktop %1", modelData.id)
                                }
                                PC3.Label {
                                    Layout.alignment: Qt.AlignHCenter
                                    font.pointSize: Kirigami.Theme.smallFont.pointSize
                                    opacity: 0.75
                                    text: modelData.windowCount > 0 ? String(modelData.windowCount) : ""
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: overviewHost.switchToWorkspace(modelData.id)
                            }
                        }

                        DropArea {
                            id: wsDrop
                            anchors.fill: parent
                            onDropped: (drop) => {
                                const addr = root.draggedAddress || drop.getDataAsString("text/x-bwm-window-address");
                                if (addr) overviewHost.moveWindowToWorkspace(addr, modelData.id);
                            }
                        }
                    }
                }

                PC3.Button {
                    icon.name: "list-add"
                    text: i18nd("kwin", "Add Desktop")
                    display: PC3.AbstractButton.IconOnly
                    PC3.ToolTip.text: text
                    PC3.ToolTip.visible: hovered
                    onClicked: overviewHost.addWorkspace()
                }
            }
        }

        // Mode header / Search bar (Overview + WindowView)
        RowLayout {
            visible: isPrimaryOverviewScreen && !root.isGrid
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: 520
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            PlasmaExtras.SearchField {
                id: searchField
                Layout.fillWidth: true
                placeholderText: root.isOverview
                    ? i18nd("kwin", "Search…")
                    : i18nd("kwin", "Filter windows…")
                text: overviewHost ? overviewHost.searchText : ""
                onTextChanged: if (overviewHost) overviewHost.searchText = text
                Keys.onReturnPressed: {
                    if (root.isOverview && text.length > 0 && milouLoader.item && milouLoader.item.count > 0) {
                        milouLoader.item.runCurrentIndex();
                        overviewHost.close();
                    } else {
                        const list = overviewHost.windowsFor(
                            root.showAllWorkspaces ? "" : screenName,
                            root.activeWsId,
                            root.showAllWorkspaces,
                            root.showAllWorkspaces
                        );
                        if (list.length > 0) {
                            const first = list[0];
                            overviewHost.activateWindow(first.address, first.workspaceId, first.minimized, first.special);
                        }
                    }
                }
                Keys.onDownPressed: if (milouLoader.item) milouLoader.item.incrementCurrentIndex()
                Keys.onUpPressed: if (milouLoader.item) milouLoader.item.decrementCurrentIndex()
            }

            // Quick toggle between Overview and Grid
            PC3.ToolButton {
                visible: root.isOverview
                icon.name: "view-grid"
                PC3.ToolTip.text: i18nd("kwin", "Desktop Grid")
                PC3.ToolTip.visible: hovered
                onClicked: overviewHost.setMode("grid")
            }
        }

        // Main content area
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // KRunner / Milou live results overlay loaded lazily when typing in Overview mode
            Rectangle {
                id: milouContainer
                visible: root.isOverview && isPrimaryOverviewScreen && searchField.text.trim().length > 0
                anchors.top: parent.top
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.min(560, parent.width * 0.8)
                height: Math.min(340, parent.height * 0.45)
                z: 50
                radius: Kirigami.Units.cornerRadius * 2
                color: Qt.rgba(Kirigami.Theme.backgroundColor.r,
                               Kirigami.Theme.backgroundColor.g,
                               Kirigami.Theme.backgroundColor.b, 0.94)
                border.width: 1
                border.color: Kirigami.Theme.highlightColor
                clip: true

                Loader {
                    id: milouLoader
                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.smallSpacing
                    active: milouContainer.visible
                    sourceComponent: Component {
                        Milou.ResultsView {
                            queryString: searchField.text.trim()
                            onActivated: overviewHost.close()
                        }
                    }
                }
            }

            // 1) Overview & WindowView: KWin ExpoLayout
            KWinEffects.ExpoLayout {
                id: mainExpo
                visible: !root.isGrid
                anchors.fill: parent
                anchors.topMargin: milouContainer.visible ? milouContainer.height + Kirigami.Units.largeSpacing : 0
                placementMode: KWinEffects.ExpoLayout.Rows

                Repeater {
                    model: overviewHost
                        ? overviewHost.windowsFor(
                            root.showAllWorkspaces ? "" : screenName,
                            root.activeWsId,
                            root.showAllWorkspaces,
                            root.showAllWorkspaces)
                        : []
                    delegate: Loader {
                        required property var modelData
                        anchors.fill: parent
                        sourceComponent: windowCardComponent
                        onLoaded: {
                            item.modelData = modelData;
                            item.targetLayout = mainExpo;
                            item.compactMode = false;
                            item.showWorkspaceBadge = root.showAllWorkspaces;
                        }
                    }
                }
            }

            // Empty state placeholder
            PlasmaExtras.PlaceholderMessage {
                anchors.centerIn: parent
                visible: !root.isGrid && !milouContainer.visible && overviewHost
                    && overviewHost.windowsFor(
                        root.showAllWorkspaces ? "" : screenName,
                        root.activeWsId,
                        root.showAllWorkspaces,
                        root.showAllWorkspaces).length === 0
                text: searchField.text.length > 0
                    ? i18nd("kwin", "No matching windows")
                    : i18nd("kwin", "No open windows")
            }

            // 2) Desktop Grid mode (Meta+G)
            GridLayout {
                id: desktopGrid
                visible: root.isGrid
                anchors.fill: parent
                columns: Math.max(2, Math.ceil(Math.sqrt(overviewHost ? overviewHost.workspaces.length : 4)))
                rowSpacing: Kirigami.Units.largeSpacing * 2
                columnSpacing: Kirigami.Units.largeSpacing * 2

                Repeater {
                    model: overviewHost ? overviewHost.workspaces : []
                    delegate: Rectangle {
                        id: gridCell
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Kirigami.Units.cornerRadius * 2
                        color: gridDrop.containsDrag
                            ? Qt.rgba(Kirigami.Theme.highlightColor.r, Kirigami.Theme.highlightColor.g, Kirigami.Theme.highlightColor.b, 0.25)
                            : Qt.rgba(Kirigami.Theme.backgroundColor.r, Kirigami.Theme.backgroundColor.g, Kirigami.Theme.backgroundColor.b, 0.72)
                        border.width: modelData.active || gridDrop.containsDrag ? 2 : 1
                        border.color: modelData.active || gridDrop.containsDrag
                            ? Kirigami.Theme.highlightColor
                            : Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.22)
                        clip: true

                        MouseArea {
                            anchors.fill: parent
                            onClicked: overviewHost.switchToWorkspace(modelData.id)
                        }

                        DropArea {
                            id: gridDrop
                            anchors.fill: parent
                            onDropped: (drop) => {
                                const addr = root.draggedAddress || drop.getDataAsString("text/x-bwm-window-address");
                                if (addr) overviewHost.moveWindowToWorkspace(addr, modelData.id);
                            }
                        }

                        PC3.Label {
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.margins: Kirigami.Units.mediumSpacing
                            font.bold: modelData.active
                            text: i18nd("kwin", "Desktop %1", modelData.id)
                            z: 5
                        }

                        KWinEffects.ExpoLayout {
                            id: cellExpo
                            anchors.fill: parent
                            anchors.topMargin: 30
                            anchors.margins: Kirigami.Units.smallSpacing
                            placementMode: KWinEffects.ExpoLayout.Rows

                            Repeater {
                                model: overviewHost
                                    ? overviewHost.windowsFor("", modelData.id, false, false)
                                    : []
                                delegate: Loader {
                                    required property var modelData
                                    anchors.fill: parent
                                    sourceComponent: windowCardComponent
                                    onLoaded: {
                                        item.modelData = modelData;
                                        item.targetLayout = cellExpo;
                                        item.compactMode = true;
                                        item.showWorkspaceBadge = false;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
