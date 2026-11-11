// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import org.bwm.kcm
import qs.modules.plasma.runtime
ThemeHost {
 property var values:({})
 contextProperties:values
 source:InterfaceTheme.state.osdSource?"file://"+InterfaceTheme.state.osdSource:""
 onStatusChanged:if(error)console.warn("Plasma OSD theme; using native OsdItem:",error)
}
