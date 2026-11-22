// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import qs.services
import org.bwm.kcm
ThemeHost {
 focus:true
 property var controller
 property string themeSource
 property string dialogImagePath: "dialogs/background"
 property var blurTarget: null
 contextProperties:({bwmController:controller,bwmToplevels:Object.fromEntries(controller.windowList.map(w=>[w.address,(w.workspace?.name==="special:minimized"||(w.workspace?.id??0)===99)?null:(w.toplevel??null)])),bwmWindows:controller.windowList.map(w=>({title:w.title,address:w.address,class:w.class,appIcon:AppSearch.guessIcon(w.class),workspace:w.workspace})),bwmDialogImagePath:dialogImagePath,bwmBlurTarget:blurTarget})
 source:themeSource?"file://"+themeSource:""
 onStatusChanged:if(error)console.warn("Plasma switcher theme; using thumbnail grid:",error)
}
