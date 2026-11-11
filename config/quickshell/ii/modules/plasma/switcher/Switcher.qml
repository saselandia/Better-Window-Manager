// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.modules.plasma.runtime
Scope {
 id:root
 required property var controller
 readonly property bool customReady:themed.item?.ready??false
 Loader {
  id:builtin;active:!root.customReady
  onActiveChanged:if(active)setSource(Qt.resolvedUrl("ThumbnailGrid.qml"),{controller:root.controller});else source=""
  Component.onCompleted:if(active)setSource(Qt.resolvedUrl("ThumbnailGrid.qml"),{controller:root.controller})
 }
 PanelWindow {
  visible:root.controller.isOpen&&root.customReady
  screen:root.controller.focusedScreen;color:"transparent"
  anchors {top:true;bottom:true;left:true;right:true}
  exclusionMode:ExclusionMode.Ignore;exclusiveZone:0
  WlrLayershell.namespace:"quickshell:altTab"
  WlrLayershell.layer:WlrLayer.Overlay
  WlrLayershell.keyboardFocus:visible?WlrKeyboardFocus.Exclusive:WlrKeyboardFocus.None
  MouseArea {anchors.fill:parent;onClicked:root.controller.cancel()}
  Loader {
   id:themed;anchors.fill:parent
   active:InterfaceTheme.state.switcherSource!==""
   onActiveChanged:loadTheme()
   Component.onCompleted:loadTheme()
   function loadTheme(){if(active)setSource(Qt.resolvedUrl("ThemedSwitcher.qml"),{controller:root.controller,themeSource:InterfaceTheme.state.switcherSource});else source="";}
   Connections {target:InterfaceTheme;function onStateChanged(){themed.loadTheme();}}
  }
 }
}
