/*
    SPDX-FileCopyrightText: 1999, 2000 Matthias Ettrich <ettrich@kde.org>
    SPDX-FileCopyrightText: 2003 Lubos Lunak <l.lunak@kde.org>
    SPDX-FileCopyrightText: 2026 BWM

    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM (F9): el menú de operaciones de la ventana de KWin (barra de título con el botón derecho,
// botón de menú de la decoración, Alt+F3), con la estructura de UserActionsMenu::init() y de sus
// submenús de escritorios y pantallas en kwin v6.7.5 (src/useractions.cpp). Las acciones van a
// kwin-window.py (F8/F9). Lo que Hyprland no tiene (mantener encima/debajo, atajo de la ventana,
// actividades) no aparece o sale desactivado; no se finge.
import QtQuick
import Quickshell
import qs.modules.common
import qs.services
import org.kde.plasma.components as PC3

PC3.Menu {
    id: root

    required property string address
    readonly property var client: PlasmaMenus.client(address)
    readonly property int workspaceCount: Math.max(1, Config.options.bar.workspaces.shown ?? 10)
    readonly property bool maximized: PlasmaMenus.hasTag(client, "bwm-maximized")
    function run(args) { PlasmaMenus.run(args.concat([root.address])); }
    function tr(text, ...args) { return MenuI18n.i18n(text, ...args); }
    function trc(context, text, ...args) { return MenuI18n.i18nc(context, text, ...args); }

    // ── initDesktopPopup(): sólo con más de un escritorio
    PC3.Menu {
        id: desktops
        title: root.tr("&Desktops")
        icon.name: "virtual-desktops"

        PC3.MenuItem {
            text: root.tr("&All Desktops")
            checkable: true
            checked: root.client?.pinned ?? false
            onTriggered: root.run(["pin"])
        }
        PC3.MenuSeparator { id: desktopsSep1 }
        DynamicItems {
            menu: desktops
            before: desktopsSep1b
            model: root.workspaceCount
            delegate: PC3.MenuItem {
                required property int index
                // Nombre de escritorio por defecto de KWin («Desktop %1»)
                text: root.tr("Desktop %1", index + 1)
                checkable: true
                checked: !(root.client?.pinned ?? false) && root.client?.workspace?.id === index + 1
                onTriggered: root.run(["to-desktop", String(index + 1)])
            }
        }
        PC3.MenuSeparator { id: desktopsSep1b }
        DynamicItems {
            menu: desktops
            before: desktopsSep2
            model: root.workspaceCount
            delegate: PC3.MenuItem {
                required property int index
                text: root.tr("Move to %1", root.tr("Desktop %1", index + 1))
                onTriggered: root.run(["to-desktop", String(index + 1)])
            }
        }
        PC3.MenuSeparator { id: desktopsSep2 }
        PC3.MenuItem {
            // Hyprland: una ventana está en un solo workspace; «Añadir» no existe
            text: root.trc("Create a new desktop and add the window to that desktop", "Add to &New Desktop")
            enabled: false
        }
        PC3.MenuItem {
            text: root.trc("Create a new desktop and move the window to that desktop", "Move to New Desktop")
            onTriggered: {
                const used = new Set(HyprlandData.windowList.map(w => w.workspace?.id));
                let n = 1;
                while (used.has(n))
                    n++;
                root.run(["to-desktop", String(n)]);
            }
        }
    }

    // ── initScreenPopup(): sólo con más de una pantalla
    PC3.Menu {
        id: screens
        title: root.tr("Move to &Screen")
        icon.name: "computer"
        DynamicItems {
            menu: screens
            model: HyprlandData.monitors
            delegate: PC3.MenuItem {
                required property var modelData
                required property int index
                text: root.trc("@item:inmenu List of all Screens to send a window to. First argument is a number, second the output identifier. E.g. Screen 1 (HDMI1)",
                               "Screen &%1 (%2)", index + 1, modelData.name)
                checkable: true
                checked: root.client?.monitor === modelData.id
                onTriggered: root.run(["to-screen", "desc:" + modelData.description])
            }
        }
    }

    PC3.MenuItem {
        text: root.tr("Ma&ximize")
        icon.name: "window-maximize"
        checkable: true
        checked: root.maximized
        onTriggered: root.run(["maximize", "--mode", "toggle"])
    }
    PC3.MenuItem {
        text: root.tr("Mi&nimize")
        icon.name: "window-minimize"
        onTriggered: root.run(["minimize"])
    }
    PC3.MenuItem {
        // Hyprland no tiene capas de apilamiento por ventana
        text: root.tr("Keep &Above Others")
        icon.name: "window-keep-above"
        checkable: true
        enabled: false
    }

    PC3.Menu {
        title: root.tr("&More Actions")
        icon.name: "overflow-menu"

        PC3.MenuItem {
            text: root.tr("&Move")
            icon.name: "transform-move"
            onTriggered: root.run(["interactive", "move"])
        }
        PC3.MenuItem {
            text: root.tr("&Resize")
            icon.name: "transform-scale"
            onTriggered: root.run(["interactive", "resize"])
        }
        PC3.MenuItem {
            text: root.tr("Keep &Below Others")
            icon.name: "window-keep-below"
            checkable: true
            enabled: false
        }
        PC3.MenuItem {
            text: root.tr("&Fullscreen")
            icon.name: "view-fullscreen"
            checkable: true
            checked: (root.client?.fullscreen ?? 0) === 2
            onTriggered: root.run(["fullscreen"])
        }
        PC3.MenuItem {
            text: root.tr("&No Titlebar and Frame")
            icon.name: "edit-none-border"
            checkable: true
            checked: PlasmaMenus.hasTag(root.client, "bwm-no-border")
            onTriggered: root.run(["no-border"])
        }
        PC3.MenuItem {
            text: root.tr("&Hide from Screenshots and Screen Recordings")
            icon.name: "view-private"
            checkable: true
            checked: PlasmaMenus.hasTag(root.client, "bwm-no-capture")
            onTriggered: root.run(["no-capture"])
        }
        PC3.MenuSeparator {}
        PC3.MenuItem {
            text: root.tr("Configure Special &Window Settings…")
            icon.name: "preferences-system-windows-actions"
            onTriggered: root.run(["rules", "window"])
        }
        PC3.MenuItem {
            text: root.tr("Configure S&pecial Application Settings…")
            icon.name: "preferences-system-windows-actions"
            onTriggered: root.run(["rules", "application"])
        }
    }

    PC3.MenuSeparator {}

    // Como KWin: los submenús de escritorios y pantallas sólo existen si hay más de uno
    Component.onCompleted: {
        if (root.workspaceCount <= 1)
            root.removeMenu(desktops);
        if (Quickshell.screens.length <= 1)
            root.removeMenu(screens);
    }

    PC3.MenuItem {
        text: root.tr("&Close")
        icon.name: "window-close"
        onTriggered: root.run(["close"])
    }
}
