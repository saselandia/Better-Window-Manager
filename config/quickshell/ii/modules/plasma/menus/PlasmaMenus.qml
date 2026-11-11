// BWM (F9 de docs/BREEZE_PLAN.md): estado de los menús contextuales de Breeze. Sólo uno abierto a
// la vez, como los QMenu de Plasma; los pinta MenuHost.qml en una capa de la pantalla donde se abren.
pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import qs.services

Singleton {
    id: root

    property string kind: ""            // window | task | desktop | panel
    property string screenName: ""
    property real x: 0                  // punto de apertura, lógico y relativo a la pantalla
    property real y: 0
    property rect anchorRect: Qt.rect(0, 0, 0, 0) // botón que lo abre (task/panel), relativo a la pantalla
    property string edge: "bottom"      // borde del panel, para colocarlo como Plasma
    property string address: ""         // window: ventana de Hyprland (0x…)
    property var group: null            // task: grupo del gestor de tareas (appId, toplevels)
    property var panelScreen: ""        // panel: pantalla del panel
    property int serial: 0

    readonly property string kwin: Quickshell.env("HOME") + "/.config/hypr/skins/plasma/scripts/kwin-window.py"
    readonly property bool opened: kind !== ""

    function screenAt(gx, gy) {
        for (const s of Quickshell.screens)
            if (gx >= s.x && gx < s.x + s.width && gy >= s.y && gy < s.y + s.height)
                return s;
        return Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? Quickshell.screens[0];
    }

    // Punto global (coordenadas de Hyprland)
    function openAt(kind, gx, gy, props) {
        const s = screenAt(gx, gy);
        openLocal(kind, s?.name ?? "", gx - (s?.x ?? 0), gy - (s?.y ?? 0), props);
    }
    // Junto a un elemento (botón del panel): debajo o encima según el borde, alineado a la izquierda
    function openFor(kind, item, edge, props) {
        const win = item.QsWindow.window;
        const p = item.mapToItem(null, 0, 0);
        const s = win?.screen;
        // La capa del panel está pegada a su borde: su origen en la pantalla sale del borde
        const e = edge || "bottom";
        const wx = e === "right" ? (s?.width ?? 0) - (win?.width ?? 0) : 0;
        const wy = e === "bottom" ? (s?.height ?? 0) - (win?.height ?? 0) : 0;
        root.anchorRect = Qt.rect(p.x + wx, p.y + wy, item.width, item.height);
        root.edge = edge || "bottom";
        openLocal(kind, s?.name ?? "", p.x + wx, p.y + wy + item.height, props, true);
    }
    function openLocal(kind, screenName, lx, ly, props, keepAnchor) {
        if (!keepAnchor)
            root.anchorRect = Qt.rect(lx, ly, 0, 0);
        root.address = props?.address ?? "";
        root.group = props?.group ?? null;
        root.panelScreen = props?.panelScreen ?? "";
        root.panelEditing = props?.editing ?? false;
        if (props?.edge)
            root.edge = props.edge;
        root.screenName = screenName;
        root.x = lx;
        root.y = ly;
        root.kind = kind;
        root.serial++;
        HyprlandData.updateWindowList();
    }
    function close() { root.kind = ""; }

    // Modo de edición del panel (F3) y su editor de elementos gráficos: los atiende el panel
    // (Panel.qml/PanelContent.qml); así este módulo no importa el del panel
    property bool panelEditing: false
    signal editModeRequested(string screenName, bool value)
    signal widgetsRequested(string screenName)
    function enterEditMode(screenName) { root.editModeRequested(screenName || root.screenName, true); }
    function openWidgets(screenName) {
        const name = screenName || root.screenName;
        root.editModeRequested(name, true);
        root.widgetsRequested(name);
    }

    // Acciones de ventana: un solo sitio, kwin-window.py (F8/F9)
    function run(args) { Quickshell.execDetached(["python3", root.kwin].concat(args)); }
    function client(address) { return HyprlandData.windowList.find(w => w.address === address) ?? null; }
    function hasTag(c, tag) { return (c?.tags ?? []).some(t => String(t).replace(/\*$/, "") === tag); }
}
