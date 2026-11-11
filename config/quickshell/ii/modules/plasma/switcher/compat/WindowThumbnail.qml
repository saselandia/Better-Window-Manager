// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import Quickshell.Widgets
import Quickshell.Wayland
Item {
 property var wId
 property var winId:wId
 ScreencopyView {anchors.fill:parent;captureSource:bwmToplevels?.[String(parent.wId)]??null;live:true}
}
