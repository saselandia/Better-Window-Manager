// BWM: preserve the public applet IPC names without loading the removed handmade views.
import QtQuick
import Quickshell
import Quickshell.Io
import qs
Scope {
    Component.onDestruction:TrayState.close()
    Connections { target:GlobalStates;function onPlasmaKickoffOpenChanged(){if(GlobalStates.plasmaKickoffOpen)TrayState.close()} }
    IpcHandler { target:"plasmaNetwork";function toggle():void{TrayState.toggle("network","")} function open():void{TrayState.open("network","")} function close():void{TrayState.close()} }
    IpcHandler { target:"plasmaBluetooth";function toggle():void{TrayState.toggle("bluetooth","")} function open():void{TrayState.open("bluetooth","")} function close():void{TrayState.close()} }
    IpcHandler { target:"plasmaAudio";function toggle():void{TrayState.toggle("audio","")} function open():void{TrayState.open("audio","")} function close():void{TrayState.close()} }
    IpcHandler { target:"plasmaCalendar";function toggle():void{TrayState.toggle("calendar","")} function open():void{TrayState.open("calendar","")} function close():void{TrayState.close()} }
    IpcHandler { target:"plasmaNotifications";function toggle():void{TrayState.toggle("notifications","")} function open():void{TrayState.open("notifications","")} function close():void{TrayState.close()} }
}
