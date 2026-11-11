// SPDX-License-Identifier: GPL-2.0-or-later
// BWM: KWin TabBox QML contract; window operations stay with AltTab's MRU controller.
import QtQuick
Item {
 id:root
 readonly property var controller:bwmController
 property var model:windows
 property var windowsData:bwmWindows
 onWindowsDataChanged:rebuild()
 property int currentIndex:controller.selectedIndex
 property rect screenGeometry:Qt.rect(0,0,controller.focusedScreen?.width??1920,controller.focusedScreen?.height??1080)
 property bool allDesktops:false
 visible:controller.isOpen
 onCurrentIndexChanged:if(controller.selectedIndex!==currentIndex)controller.selectedIndex=currentIndex
 ListModel {
  id:windows;dynamicRoles:true
  function activate(index){root.controller.selectWindow(index);}
  function close(index){const w=root.windowsData[index];if(w)root.controller.closeWindow(w.address);}
 }
 function rebuild() {
  windows.clear();
  for(const w of windowsData) windows.append({caption:w.title??"",icon:w.appIcon??w.class??"",windowId:w.address,closeable:true,desktopName:String(w.workspace?.id??1),minimized:w.workspace?.name==="special:minimized"});
 }
 Connections {target:root.controller;function onSelectedIndexChanged(){root.currentIndex=root.controller.selectedIndex;}}
 Component.onCompleted:rebuild()
}
