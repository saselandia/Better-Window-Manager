// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import qs.services
import org.bwm.kcm
ThemeHost {
 focus:true
 property var controller
 property string themeSource
 contextProperties:({bwmController:controller,bwmToplevels:Object.fromEntries(controller.windowList.map(w=>[w.address,w.toplevel??null])),bwmWindows:controller.windowList.map(w=>({title:w.title,address:w.address,class:w.class,appIcon:AppSearch.guessIcon(w.class),workspace:w.workspace}))})
 source:themeSource?"file://"+themeSource:""
 onStatusChanged:if(error)console.warn("Plasma switcher theme; using thumbnail grid:",error)
}
