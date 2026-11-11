// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import org.bwm.kcm
ThemeHost {
 function configure(path,context,authenticator,userName) {
  source="";
  contextProperties={authenticator:authenticator,kscreenlocker_userName:userName,kscreenlocker_userImage:"",org_kde_plasma_screenlocker_greeter_interfaceVersion:2};
  source=path?"file://"+path:"";
 }
 onStatusChanged:if(error)console.warn("Plasma lock theme; using Breeze:",error)
 // Qt.quit() only emits quitRequested in this separate engine; LockContext alone unlocks BWM.
}
