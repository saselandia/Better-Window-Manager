// BWM: adapter replacing org.kde.taskmanager.TasksModel (KWin protocol) with Quickshell toplevels.
import QtQuick
import Quickshell
import qs.services
import qs.modules.common
import "PanelLogic.js" as Logic
QtObject {
    id: root
    property var order: Config.options.bar.plasma.taskOrder ?? []
    readonly property var groups: {
        const values=TaskbarApps.apps.filter(a=>a.appId!=="SEPARATOR");
        return values.slice().sort((a,b)=>{
            const ai=root.order.indexOf(a.appId), bi=root.order.indexOf(b.appId);
            return (ai<0 ? values.indexOf(a)+root.order.length:ai) - (bi<0 ? values.indexOf(b)+root.order.length:bi);
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
    function launch(appId) { entry(appId)?.execute(); }
    function activate(top) {
        if(!top) return;
        if(minimized(top)) Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/toggle-minimize.py","restore",address(top)]);
        else top.activate();
    }
    function click(group) {
        const tops=group.toplevels;
        if(!tops.length) { launch(group.appId); return; }
        if(tops.length===1 && tops[0].activated) {
            Quickshell.execDetached(["/home/sasel/.config/hypr/scripts/toggle-minimize.py","min",address(tops[0])]);
        } else cycle(group,1);
    }
    function cycle(group,step) {
        const tops=group.toplevels;
        if(!tops.length) return;
        const index=tops.findIndex(t=>t.activated);
        activate(tops[(index+step+tops.length)%tops.length]);
    }
}
