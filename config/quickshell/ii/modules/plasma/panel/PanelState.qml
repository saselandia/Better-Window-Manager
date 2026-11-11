pragma Singleton
import QtQuick
import Quickshell
import qs
import qs.services
import qs.modules.common
import "PanelLogic.js" as Logic
Singleton {
    id: root
    readonly property var configuration: Config.options.bar.plasma
    property var panels: ({})
    property var editing: ({})
    function edgeFor(screenName) { return Logic.edge(configuration, Config.options.bar.bottom); }
    function update(screenName, values) { panels = Object.assign({}, panels, {[screenName]: values}); }
    function remove(screenName) { const copy=Object.assign({},panels); delete copy[screenName]; panels=copy; }
    function gapFor(screenName) { return panels[screenName]?.gap ?? 0; }
    function distanceFor(screenName) { return panels[screenName]?.distance ?? Number(configuration.thickness || Config.options.bar.height || 44); }
    function setEditing(screenName, value) { editing=Object.assign({},editing,{[screenName]:value}); }
    function anchor(button, name) {
        const p = button.mapToItem(null, button.width/2, button.height/2);
        GlobalStates.plasmaPopupAnchorY = p.y;
        GlobalStates[name+"AnchorX"] = p.x;
        GlobalStates[name+"Screen"] = button.QsWindow.window?.screen?.name ?? "";
    }
    Timer {
        interval:700; repeat:true; running:Appearance.isPlasma
        onTriggered: { HyprlandData.updateWindowList(); HyprlandData.updateMonitors(); }
    }
}
