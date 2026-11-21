/*
    SPDX-FileCopyrightText: 2026 BWM
    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM (F9): anfitrión de los menús contextuales de Breeze. Los menús de Plasma son QMenu (Qt
// Widgets), que no pueden abrirse desde layer-shell (F4); aquí son PC3.Menu de QtQuick, con el
// estilo de Plasma activo, dentro de una capa transparente a pantalla completa de la pantalla donde
// se abren. Pulsar fuera o Escape lo cierran, como un QMenu.
//
// IPC (el plugin breezebars, Alt+F3 y kwin-window.py menu):
//   qs -c ii ipc call plasmaWindowMenu open <dirección> <x> <y>    (coordenadas globales)
//   qs -c ii ipc call plasmaWindowMenu close
//   qs -c ii ipc call plasmaMenus inspect                           (pruebas: tipo y entradas)
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import org.kde.plasma.components as PC3
import qs.modules.plasma.theme
import qs.modules.plasma.tray as PlasmaTray

Scope {
    id: root

    // El menú abierto (pruebas: tests/test_plasma_menus_ui.py)
    readonly property var menu: loader.item
    readonly property int blurRegionCount: _blurRegions.length
    property var _trackedMenus: []
    property var _blurRegions: []

    BlurPath { id: menuBgPath; path: "widgets/background" }
    Component { id: blurRegionComp; Region {} }
    Connections {
        target: PlasmaTheme
        function onBlurChanged() { root.updateBlurRegions(); }
    }

    function trackMenu(m) {
        if (!m || root._trackedMenus.indexOf(m) >= 0)
            return;
        root._trackedMenus.push(m);
        if (m.background && m.background.hasOwnProperty("imagePath"))
            m.background.imagePath = Qt.binding(() => menuBgPath.resolved);
        m.openedChanged.connect(root.updateBlurRegions);
        if (m.contentModel && m.contentModel.countChanged)
            m.contentModel.countChanged.connect(() => { root.trackSubmenus(m); root.updateBlurRegions(); });
        root.trackSubmenus(m);
    }

    function trackSubmenus(m) {
        if (!m)
            return;
        for (let i = 0; i < m.count; ++i) {
            const sub = m.itemAt(i)?.subMenu ?? (typeof m.menuAt === "function" ? m.menuAt(i) : null);
            if (sub)
                root.trackMenu(sub);
        }
    }

    function updateBlurRegions() {
        const next = [];
        if (PlasmaTheme.blur && PlasmaMenus.opened) {
            for (const m of root._trackedMenus) {
                if (m)
                    root.trackSubmenus(m);
                if (m && m.opened && m.background)
                    next.push(blurRegionComp.createObject(win, { item: m.background }));
            }
        }
        const prev = root._blurRegions;
        root._blurRegions = next;
        blurRoot.regions = next;
        for (const r of prev)
            r.destroy();
    }

    IpcHandler {
        target: "plasmaWindowMenu"
        function open(address: string, x: string, y: string): void {
            PlasmaMenus.openAt("window", Number(x), Number(y), { address: address.startsWith("0x") ? address : "0x" + address });
        }
        function close(): void { PlasmaMenus.close(); }
    }
    IpcHandler {
        target: "plasmaMenus"
        function inspect(): string {
            const m = loader.item;
            const items = [];
            if (m)
                for (let i = 0; i < m.count; ++i) {
                    const it = m.itemAt(i);
                    if (it && it.visible !== false)
                        items.push((it.subMenu ? "▸ " : "") + (it.text ?? (it.title ?? "—")) + (it.checkable ? (it.checked ? " [x]" : " [ ]") : "") + (it.enabled === false ? " (off)" : ""));
                }
            return JSON.stringify({ kind: PlasmaMenus.kind, screen: PlasmaMenus.screenName, opened: m?.opened ?? false,
                                    x: m?.x ?? -1, y: m?.y ?? -1, width: m?.width ?? -1, height: m?.height ?? -1, items: items });
        }
        function close(): void { PlasmaMenus.close(); }
    }

    PanelWindow {
        id: win
        visible: PlasmaMenus.opened
        screen: Quickshell.screens.find(s => s.name === PlasmaMenus.screenName) ?? Quickshell.screens[0]
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "quickshell:plasmaMenu"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: PlasmaMenus.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        anchors { top: true; bottom: true; left: true; right: true }
        // KWin's blur behind the open menu and any open submenu (widgets/background translucent)
        BackgroundEffect.blurRegion: Region { id: blurRoot }

        // Pulsar fuera del menú lo cierra (el menú también lo hace; esto cubre los huecos)
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onPressed: PlasmaMenus.close()
        }

        Item {
            id: host
            anchors.fill: parent
            focus: true
            Keys.onEscapePressed: PlasmaMenus.close()
        }

        Loader {
            id: loader
            property int serial: PlasmaMenus.serial
            onSerialChanged: { active = false; active = PlasmaMenus.opened; }
            active: false
            sourceComponent: ({ window: windowMenu, task: taskMenu, desktop: desktopMenu, panel: panelMenu, tray: trayMenu })[PlasmaMenus.kind] ?? null
            onLoaded: Qt.callLater(root.show)
        }
        Connections {
            target: PlasmaMenus
            function onOpenedChanged() {
                if (!PlasmaMenus.opened) {
                    loader.active = false;
                    root._trackedMenus = [];
                    root.updateBlurRegions();
                }
            }
        }
    }

    // Como PlasmaExtras.Menu: en el punto pedido; desde un botón del panel, pegado al botón por el
    // lado de la pantalla (TopPosedLeftAlignedPopup con el panel abajo, etc.)
    function show() {
        const m = loader.item;
        if (!m)
            return;
        m.parent = host;
        root._trackedMenus = [];
        root.trackMenu(m);
        m.closed.connect(() => { if (loader.item === m) PlasmaMenus.close(); });
        m.popup(host, PlasmaMenus.x, PlasmaMenus.y);
        root.place(m);
        root.updateBlurRegions();
        // Las entradas que llegan después (recientes, D-Bus menu) cambian el tamaño: se recoloca
        m.heightChanged.connect(() => root.place(m));
        m.widthChanged.connect(() => root.place(m));
    }
    function place(m) {
        if (PlasmaMenus.kind === "task" || PlasmaMenus.kind === "panel" || PlasmaMenus.kind === "tray") {
            const r = PlasmaMenus.anchorRect;
            const e = PlasmaMenus.edge;
            if (e === "bottom") { m.x = r.x; m.y = r.y - m.height; }
            else if (e === "top") { m.x = r.x; m.y = r.y + r.height; }
            else if (e === "left") { m.x = r.x + r.width; m.y = r.y; }
            else { m.x = r.x - m.width; m.y = r.y; }
            m.x = Math.max(0, Math.min(m.x, win.width - m.width));
            m.y = Math.max(0, Math.min(m.y, win.height - m.height));
        } else if (win.width > 0 && win.height > 0) {
            m.x = Math.max(0, Math.min(m.x, win.width - m.width));
            m.y = Math.max(0, Math.min(m.y, win.height - m.height));
        }
    }

    Component { id: windowMenu; WindowMenu { parent: host; address: PlasmaMenus.address } }
    Component { id: taskMenu; TaskMenu { parent: host; group: PlasmaMenus.group } }
    Component { id: desktopMenu; DesktopMenu { parent: host } }
    Component { id: panelMenu; PanelMenu { parent: host; panelScreen: PlasmaMenus.panelScreen } }
    Component {
        id: trayMenu
        PlasmaTray.TrayMenu {
            parent: host
            handle: PlasmaMenus.trayMenu?.menu !== undefined ? PlasmaMenus.trayMenu.menu : PlasmaMenus.trayMenu
            mockEntries: PlasmaMenus.trayMenu?.mockEntries ?? null
        }
    }
}
