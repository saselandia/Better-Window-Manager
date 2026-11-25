// BWM: adapter replacing org.kde.taskmanager.TasksModel (KWin protocol) with Quickshell toplevels.
import QtQuick
import Quickshell
import qs.services
import qs.modules.common
import "PanelLogic.js" as Logic
QtObject {
    id: root
    property var panelMonitor: null
    property var order: Config.options.bar.plasma.taskOrder ?? []
    readonly property var taskSettings: Config.options.bar.plasma.taskManager ?? ({})
    readonly property bool wheelEnabled: taskSettings.wheelEnabled ?? true
    readonly property var groups: {
        const values=TaskbarApps.apps.filter(a=>a.appId!=="SEPARATOR");
        const sorted=values.slice().sort((a,b)=>{
            const ai=root.order.indexOf(a.appId), bi=root.order.indexOf(b.appId);
            return (ai<0 ? values.indexOf(a)+root.order.length:ai) - (bi<0 ? values.indexOf(b)+root.order.length:bi);
        });
        return Logic.filterTasks(sorted, root.taskSettings, {
            monitorId: root.panelMonitor?.id,
            workspaceId: root.panelMonitor?.activeWorkspace?.id,
            clientFor: top => root.client(top),
            isMinimized: top => root.minimized(top)
        });
    }
    function move(source,target) {
        Config.options.bar.plasma.taskOrder=Logic.reorder(groups.map(a=>a.appId),source,target);
        const pins=Config.options.dock.pinnedApps;
        const sourcePin=pins.find(id=>id.toLowerCase()===source);
        const targetPin=pins.find(id=>id.toLowerCase()===target);
        if(sourcePin && targetPin) Config.options.dock.pinnedApps=Logic.reorder(pins,sourcePin,targetPin);
    }
    function client(top) { return HyprlandData.clientForToplevel(top); }
    function address(top) { return client(top)?.address ?? ""; }
    function minimized(top) { return client(top)?.workspace?.name==="special:minimized"; }
    function entry(appId) {
        const key=appId.toLowerCase().replace(/\.desktop$/,"");
        return DesktopEntries.applications.values.find(d=>d.id.toLowerCase().replace(/\.desktop$/,"")===key)
            ?? DesktopEntries.heuristicLookup(appId);
    }
    function launch(appId) { AppSearch.launch(entry(appId)); }
    function activate(top) {
        if(!top) return;
        const window = client(top);
        if (window?.address && window.pid) {
            Quickshell.execDetached(["/home/sasel/.config/hypr/skins/plasma/scripts/kwin-window.py", "--pid", String(window.pid), "focus", window.address]);
        } else top.activate();
    }
    // BWM: Hyprland keeps a window minimized to special:minimized as the active one when nothing else
    // takes focus (alone on its workspace, pointer over the panel), so its toplevel stays "activated".
    // KWin never reports a minimized window as active: neither does this adapter.
    function isActive(top) { return !!top?.activated && !minimized(top); }
    function click(group) {
        const tops=group.toplevels;
        if(!tops.length) { launch(group.appId); return; }
        if(tops.length===1 && isActive(tops[0])) {
            Quickshell.execDetached(["/home/sasel/.config/hypr/skins/plasma/scripts/kwin-window.py","minimize",address(tops[0])]);
        } else cycle(group,1);
    }
    function cycle(group,step) {
        const tops=group.toplevels;
        if(!tops.length) return;
        const index=tops.findIndex(t=>root.isActive(t));
        activate(tops[(index+step+tops.length)%tops.length]);
    }
}
