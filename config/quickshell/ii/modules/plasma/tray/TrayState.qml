pragma Singleton
// BWM: one expanded tray/app page for the whole session, with monitor-local anchoring.
import QtQuick
import Quickshell
import Quickshell.Hyprland
import qs
Singleton {
    id:state
    property bool expanded:false
    property string screenName:""
    property string applet:""
    onAppletChanged:GlobalStates.plasmaNotificationsOpen=expanded&&applet==="notifications"
    onExpandedChanged:GlobalStates.plasmaNotificationsOpen=expanded&&applet==="notifications"
    function open(id,screen) { GlobalStates.plasmaKickoffOpen=false; screenName=screen||Hyprland.focusedMonitor?.name||Quickshell.screens[0]?.name||"";applet=id;expanded=true; }
    function close() { expanded=false; }
    function toggle(id,screen) { if(expanded&&applet===id&&(!screen||screenName===screen))close();else open(id,screen); }
}
