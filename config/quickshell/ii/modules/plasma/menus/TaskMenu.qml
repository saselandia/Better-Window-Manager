/*
    SPDX-FileCopyrightText: 2012-2016 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2016 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2026 BWM

    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM (F9): el menú contextual del gestor de tareas de Plasma 6.7.5
// (plasma-desktop/applets/taskmanager/qml/ContextMenu.qml), con su orden y sus textos:
// archivos recientes y acciones del .desktop, controles multimedia, Abrir una ventana nueva, Mover al
// escritorio, Anclar/Desanclar, Más (mover, redimensionar, maximizar, minimizar, pantalla completa,
// sin barra, ocultar de capturas), Entrar en el modo de edición y Cerrar.
// Cambios BWM: PC3.Menu en vez de PlasmaExtras.Menu (QMenu no abre desde layer-shell, F4); el
// modelo de tareas es el de Quickshell (TasksModel.qml de F3) en vez de TaskManager.TasksModel; los
// recientes salen de recently-used.xbel (task-recents.py) en vez del backend del applet; sin
// actividades ni «Lugares»; las acciones de ventana van a kwin-window.py. Encima/debajo y enrollar
// no existen en Hyprland: no aparecen.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Mpris
import qs.modules.common
import qs.services
import org.kde.plasma.components as PC3

PC3.Menu {
    id: root

    required property var group
    readonly property string appId: group?.appId ?? ""
    readonly property var toplevels: group?.toplevels ?? []
    readonly property var clients: toplevels.map(t => HyprlandData.clientForToplevel(t)).filter(c => c)
    readonly property bool isLauncher: clients.length === 0
    readonly property bool isGroup: clients.length > 1
    readonly property var target: clients.length === 1 ? clients[0] : null
    readonly property var entry: {
        const key = appId.toLowerCase().replace(/\.desktop$/, "");
        return DesktopEntries.applications.values.find(d => d.id.toLowerCase().replace(/\.desktop$/, "") === key)
            ?? DesktopEntries.heuristicLookup(appId);
    }
    readonly property int workspaceCount: Math.max(1, Config.options.bar.workspaces.shown ?? 10)
    readonly property var player: {
        const key = appId.toLowerCase().replace(/\.desktop$/, "");
        return Mpris.players.values.find(p => (p.desktopEntry ?? "").toLowerCase() === key
            || (p.identity ?? "").toLowerCase() === (entry?.name ?? "").toLowerCase()) ?? null;
    }
    property var recents: []

    function trc(context, text, ...args) { return MenuI18n.i18nc(context, text, ...args); }
    function tr(text, ...args) { return MenuI18n.i18n(text, ...args); }
    function runAll(args) { for (const c of root.clients) PlasmaMenus.run(args.concat([c.address])); }
    function runOne(args) { if (root.target) PlasmaMenus.run(args.concat([root.target.address])); }

    // Archivos recientes de la app (en Plasma: backend.recentDocumentActions)
    Process {
        running: root.appId !== ""
        command: ["python3", Quickshell.env("HOME") + "/.config/hypr/skins/plasma/scripts/task-recents.py", "list", root.appId]
        stdout: StdioCollector { onStreamFinished: { try { root.recents = JSON.parse(text); } catch (e) { root.recents = []; } } }
    }

    // ── Secciones dinámicas (loadDynamicLaunchActions): recientes, acciones, multimedia
    PC3.MenuItem {
        id: recentHeader
        text: root.trc("@title:group for section of menu items", "Recent Files")
        enabled: false; font.bold: true
        visible: root.recents.length > 0
        height: visible ? implicitHeight : 0
    }
    DynamicItems {
        menu: root
        before: actionsHeader
        model: root.recents
        delegate: PC3.MenuItem {
            required property var modelData
            text: modelData.name
            icon.name: "document-open-recent"
            onTriggered: Quickshell.execDetached(["python3", Quickshell.env("HOME") + "/.config/hypr/skins/plasma/scripts/task-recents.py",
                                                  "open", root.appId, modelData.uri])
        }
    }
    PC3.MenuItem {
        id: actionsHeader
        // Como el original: sin cabecera «Acciones» si el menú sólo tiene acciones
        text: root.trc("@title:group for section of menu items", "Actions")
        enabled: false; font.bold: true
        visible: root.recents.length > 0 && (root.entry?.actions?.length ?? 0) > 0
        height: visible ? implicitHeight : 0
    }
    DynamicItems {
        menu: root
        before: mediaPrevious
        model: root.entry?.actions ?? []
        delegate: PC3.MenuItem {
            required property var modelData
            text: modelData.name
            icon.name: modelData.icon || ""
            onTriggered: modelData.execute()
        }
    }
    PC3.MenuSeparator {
        visible: (root.entry?.actions?.length ?? 0) > 0 || root.recents.length > 0
        height: visible ? implicitHeight : 0
    }

    // Controles multimedia, como el original: sólo si la app tiene un reproductor y no es un grupo
    readonly property bool showMedia: root.player !== null && (root.player.canControl ?? true) && !root.isGroup
    PC3.MenuItem {
        id: mediaPrevious
        visible: root.showMedia; height: visible ? implicitHeight : 0
        text: root.trc("Play previous track", "Previous Track")
        icon.name: "media-skip-backward"
        enabled: root.player?.canGoPrevious ?? false
        onTriggered: root.player.previous()
    }
    PC3.MenuItem {
        visible: root.showMedia; height: visible ? implicitHeight : 0
        text: root.player?.isPlaying && root.player?.canPause ? root.trc("Pause playback", "Pause") : root.trc("Start playback", "Play")
        icon.name: root.player?.isPlaying ? "media-playback-pause" : "media-playback-start"
        enabled: root.player?.isPlaying ? (root.player?.canPause ?? false) : (root.player?.canPlay ?? false)
        onTriggered: root.player.togglePlaying()
    }
    PC3.MenuItem {
        visible: root.showMedia; height: visible ? implicitHeight : 0
        text: root.trc("Play next track", "Next Track")
        icon.name: "media-skip-forward"
        enabled: root.player?.canGoNext ?? false
        onTriggered: root.player.next()
    }
    PC3.MenuItem {
        visible: root.showMedia; height: visible ? implicitHeight : 0
        text: root.trc("Stop playback", "Stop")
        icon.name: "media-playback-stop"
        enabled: root.player?.canControl ?? false
        onTriggered: root.player.stop()
    }
    PC3.MenuSeparator { visible: root.showMedia; height: visible ? implicitHeight : 0 }

    PC3.MenuItem {
        visible: root.entry !== null; height: visible ? implicitHeight : 0
        text: root.trc("action:inmenu", "Open New Window")
        icon.name: "window-new"
        onTriggered: root.entry.execute()
    }

    PC3.Menu {
        id: desktops
        title: root.trc("action:inmenu", "Move to &Desktop")
        icon.name: "virtual-desktops"
        PC3.MenuItem {
            text: root.trc("action:inmenu", "Move &To Current Desktop")
            enabled: root.clients.some(c => c.workspace?.id !== HyprlandData.activeWorkspace?.id)
            onTriggered: root.runAll(["to-desktop", String(HyprlandData.activeWorkspace?.id ?? 1)])
        }
        PC3.MenuItem {
            text: root.trc("action:inmenu", "&All Desktops")
            checkable: true
            checked: root.clients.length > 0 && root.clients.every(c => c.pinned)
            onTriggered: root.runAll(["pin"])
        }
        PC3.MenuSeparator { id: desktopsSep }
        DynamicItems {
            menu: desktops
            before: newDesktop
            model: root.workspaceCount
            delegate: PC3.MenuItem {
                required property int index
                text: (index + 1) + ". " + root.tr("Desktop %1", index + 1)
                checkable: true
                checked: root.clients.length > 0 && root.clients.every(c => !c.pinned && c.workspace?.id === index + 1)
                onTriggered: root.runAll(["to-desktop", String(index + 1)])
            }
        }
        PC3.MenuSeparator {}
        PC3.MenuItem {
            id: newDesktop
            text: root.trc("action:inmenu", "&New Desktop")
            icon.name: "list-add"
            onTriggered: {
                const used = new Set(HyprlandData.windowList.map(w => w.workspace?.id));
                let n = 1;
                while (used.has(n))
                    n++;
                root.runAll(["to-desktop", String(n)]);
            }
        }
    }

    PC3.MenuItem {
        id: pinItem
        readonly property bool pinned: TaskbarApps.isPinned(root.appId)
        visible: root.appId !== ""; height: visible ? implicitHeight : 0
        text: pinned ? root.trc("action:inmenu", "Unpin from Task Manager") : root.trc("action:inmenu", "&Pin to Task Manager")
        icon.name: pinned ? "window-unpin" : "window-pin"
        onTriggered: TaskbarApps.togglePin(root.appId)
    }

    PC3.Menu {
        id: more
        title: root.trc("item:inmenu opens submenu", "More")
        icon.name: "view-more-symbolic"
        PC3.MenuItem {
            enabled: root.target !== null
            text: root.trc("action:inmenu", "&Move")
            icon.name: "transform-move"
            onTriggered: root.runOne(["interactive", "move"])
        }
        PC3.MenuItem {
            enabled: root.target !== null
            text: root.trc("action:inmenu", "Re&size")
            icon.name: "transform-scale"
            onTriggered: root.runOne(["interactive", "resize"])
        }
        PC3.MenuItem {
            enabled: root.target !== null
            text: root.trc("action:inmenu", "Ma&ximize")
            icon.name: "window-maximize"
            checkable: true
            checked: PlasmaMenus.hasTag(root.target, "bwm-maximized")
            onTriggered: root.runOne(["maximize", "--mode", "toggle"])
        }
        PC3.MenuItem {
            enabled: root.target !== null
            text: root.trc("action:inmenu", "Mi&nimize")
            icon.name: "window-minimize"
            checkable: true
            checked: root.target?.workspace?.name === "special:minimized"
            onTriggered: root.runOne(["toggle-minimize"])
        }
        PC3.MenuItem {
            enabled: root.target !== null
            text: root.trc("action:inmenu", "&Fullscreen")
            icon.name: "view-fullscreen"
            checkable: true
            checked: (root.target?.fullscreen ?? 0) === 2
            onTriggered: root.runOne(["fullscreen"])
        }
        PC3.MenuItem {
            enabled: root.target !== null
            text: root.trc("@action:inmenu", "&No Titlebar and Frame")
            icon.name: "edit-none-border"
            checkable: true
            checked: PlasmaMenus.hasTag(root.target, "bwm-no-border")
            onTriggered: root.runOne(["no-border"])
        }
        PC3.MenuItem {
            enabled: root.target !== null
            text: root.trc("@action:inmenu", "&Hide from Screencast")
            icon.name: "view-private"
            checkable: true
            checked: PlasmaMenus.hasTag(root.target, "bwm-no-capture")
            onTriggered: root.runOne(["no-capture"])
        }
    }

    PC3.MenuSeparator {}

    PC3.MenuItem {
        // editModeAction del contenedor: el modo de edición del panel (F3)
        text: root.tr("Enter Edit Mode")
        icon.name: "document-edit"
        onTriggered: PlasmaMenus.enterEditMode(PlasmaMenus.screenName)
    }

    PC3.MenuSeparator {}

    PC3.MenuItem {
        id: closeItem
        visible: !root.isLauncher; height: visible ? implicitHeight : 0
        text: root.isGroup ? root.trc("@action:inmenu", "&Close All") : root.trc("@action:inmenu", "&Close")
        icon.name: "window-close"
        onTriggered: root.runAll(["close"])
    }

    // Lanzador anclado sin ventanas: ni escritorios ni «Más», como el original
    Component.onCompleted: {
        if (root.isLauncher) {
            root.removeMenu(desktops);
            root.removeMenu(more);
        } else if (root.workspaceCount <= 1) {
            root.removeMenu(desktops);
        }
    }
}
