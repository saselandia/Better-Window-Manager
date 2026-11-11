// SPDX-License-Identifier: GPL-2.0-or-later
// BWM: KScreenLocker 6.7.5 authentication controls, with Breeze's shared Clock.
import QtQuick
import QtQuick.Layouts
import Quickshell
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PC3
import org.kde.breeze.components as BreezeComponents
import qs.modules.common
import qs.modules.plasma.runtime
Item {
 id:root
 required property var context
 readonly property string userName:Quickshell.env("USER")
 Authenticator {
  id:authenticator
  busy:root.context.unlockInProgress
  fingerprintsConfigured:root.context.fingerprintsConfigured
  showFailure:root.context.showFailure
  onAuthenticateRequested:root.context.tryUnlock(false)
  onResponseSubmitted:text=>root.context.currentText=text
  onClearRequested:root.context.clearText()
 }
 Rectangle {anchors.fill:parent;color:Kirigami.Theme.backgroundColor}
 Image {anchors.fill:parent;source:Config.options.background.wallpaperPath;fillMode:Image.PreserveAspectCrop;asynchronous:true;opacity:0.35}
 Item {
  anchors.fill:parent
  visible:!(customTheme.item?.ready??false)
  BreezeComponents.Clock {anchors.horizontalCenter:parent.horizontalCenter;y:parent.height*0.07}
  BreezeComponents.SessionManagementScreen {
   anchors.fill:parent
   anchors.topMargin:parent.height*0.18
   userListModel:[{name:root.userName,realName:root.userName,icon:InterfaceTheme.state.userImage?"file://"+InterfaceTheme.state.userImage:""}]
   userListCurrentIndex:0
   actionItemsVisible:true
   actionItems: BreezeComponents.ActionButton {
    text:qsTr("Unlock");icon.name:"unlock"
    enabled:!root.context.unlockInProgress
    onClicked:root.context.tryUnlock(false)
   }
   Greeter {context:root.context;userName:"";switchUserEnabled:false;showUnlockButton:false;showSessionLabel:false;Layout.alignment:Qt.AlignHCenter}
  }
 }

 Loader {
  id:customTheme;anchors.fill:parent
  active:InterfaceTheme.state.lockSource!==""
  source:active?Qt.resolvedUrl("LockTheme.qml"):""
  onLoaded:item.configure(InterfaceTheme.state.lockSource,root.context,authenticator,root.userName)
  Connections {target:InterfaceTheme;function onStateChanged(){if(customTheme.item)customTheme.item.configure(InterfaceTheme.state.lockSource,root.context,authenticator,root.userName);}}
 }
}
