// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import Quickshell.Widgets
import Quickshell.Wayland
Item {
 property var wId
 property var winId:wId
 // Temporary containment: see docs/BREEZE_RECOVERY.md.
 ScreencopyView { anchors.fill:parent; captureSource:null; live:false }
}
