/*
    SPDX-FileCopyrightText: 2012 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2014 David Edmundson <davidedmundson@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: GPL-2.0-or-later

    The part of plasma-desktop 6.7.5 desktoppackage/contents/views/Desktop.qml that the
    installed, unmodified explorer/WidgetExplorer.qml expects from its view: the root id
    with widgetExplorer, pendingUninstallTimer and the side panel Dialog with its Loader.
    BWM (no DesktopView here): the side panel is placed as a layer by WidgetExplorerView,
    which also sets contentHeight from the height the compositor configures.
*/
import QtQuick
import org.kde.plasma.core as PlasmaCore

Item {
    id: root

    property QtObject containment
    property url explorerSource
    property QtObject widgetExplorer
    // BWM: height of the Loader, from the configured layer height minus the frame.
    property real contentHeight: 600
    readonly property alias sidePanel: sidePanel
    readonly property string explorerState: sidePanelStack.state

    function toggleWidgetExplorer(containment) {
        if (sidePanelStack.state === "widgetExplorer") {
            sidePanelStack.state = "closed";
        } else {
            sidePanelStack.state = "widgetExplorer";
            sidePanelStack.setSource(root.explorerSource, {
                containment,
                sidePanel,
            });
        }
    }

    function close() {
        sidePanelStack.state = "closed";
    }

    Timer {
        id: pendingUninstallTimer
        // keeps track of the applets the user wants to uninstall
        property list<string> applets: []
        function uninstall() {
            for (const applet of applets) {
                widgetExplorer.uninstall(applet);
            }
            applets = [];

            if (sidePanelStack.state !== "widgetExplorer" && widgetExplorer) {
                widgetExplorer.destroy();
                widgetExplorer = null;
            }
        }

        interval: 60000 // one minute
        onTriggered: uninstall()
    }

    PlasmaCore.Dialog {
        id: sidePanel
        objectName: "bwmWidgetExplorerPanel"

        readonly property bool sideBarOnRightEdge: {
            if (!sidePanelStack.active) {
                return false;
            }
            const item = sidePanelStack.item;
            if (!item) {
                return false;
            }
            return (item.containment && item.containment.location == PlasmaCore.Types.RightEdge)
                || Application.layoutDirection === Qt.RightToLeft;
        }

        location: sideBarOnRightEdge ? PlasmaCore.Types.RightEdge : PlasmaCore.Types.LeftEdge
        type: PlasmaCore.Dialog.Dock
        flags: Qt.WindowStaysOnTopHint

        hideOnWindowDeactivate: true

        onVisibleChanged: {
            if (!visible) {
                sidePanelStack.state = "closed";
            }
        }

        mainItem: Loader {
            id: sidePanelStack
            asynchronous: true
            width: item ? item.width : 0
            height: Math.max(1, root.contentHeight)
            state: "closed"

            function bindingWithItem(callback: var, defaults: var): var {
                return Qt.binding(() => {
                    const item = this.item;
                    return item !== null ? callback(item) : defaults;
                });
            }

            LayoutMirroring.enabled: Application.layoutDirection === Qt.RightToLeft
            LayoutMirroring.childrenInherit: true

            onLoaded: {
                if (item) {
                    item.closed.connect(() => {
                        state = "closed";
                    });
                    sidePanel.hideOnWindowDeactivate = bindingWithItem(item => !item.preventWindowHide, false);
                    sidePanel.opacity = bindingWithItem(item => item.opacity, 1);
                    sidePanel.outputOnly = bindingWithItem(item => item.outputOnly, false);
                }
                sidePanel.visible = true;
            }
            onStateChanged: {
                if (state === "closed") {
                    sidePanel.visible = false;
                    source = ""; //unload all elements
                }
            }
        }
    }
}
