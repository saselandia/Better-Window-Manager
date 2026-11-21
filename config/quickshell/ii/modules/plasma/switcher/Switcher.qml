// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.modules.plasma.runtime
import qs.modules.plasma.theme
Scope {
 id:root
 required property var controller
 readonly property bool customReady:themed.item?.ready??false
 BlurPath { id:switcherPath; path:"dialogs/background" }
 QtObject { id:themedBlur; property Item frame:null }
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
  // KWin's blur behind a third-party TabBox theme's Dialog frame
  BackgroundEffect.blurRegion:Region { item:PlasmaTheme.blur&&root.controller.isOpen&&root.customReady?themedBlur.frame:null }
  MouseArea {anchors.fill:parent;onClicked:root.controller.cancel()}
  Loader {
   id:themed;anchors.fill:parent
   active:InterfaceTheme.state.switcherSource!==""
   onActiveChanged:loadTheme()
   Component.onCompleted:loadTheme()
   onLoaded:if(item){item.dialogImagePath=Qt.binding(()=>switcherPath.resolved);item.blurTarget=themedBlur;}
   function loadTheme(){if(active)setSource(Qt.resolvedUrl("ThemedSwitcher.qml"),{controller:root.controller,themeSource:InterfaceTheme.state.switcherSource,dialogImagePath:switcherPath.resolved,blurTarget:themedBlur});else source="";}
   Connections {target:InterfaceTheme;function onStateChanged(){themed.loadTheme();}}
  }
 }
}
