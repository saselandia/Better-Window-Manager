// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import Quickshell.Widgets
import Quickshell.Wayland
Item {
 property var wId
 property var winId:wId
 readonly property var resolvedSource: (visible && (typeof bwmController !== "undefined" ? !!bwmController?.isOpen : true))
  ? (typeof bwmToplevels !== "undefined" ? (bwmToplevels?.[String(winId)] ?? null) : null) : null
 ScreencopyView { anchors.fill:parent; captureSource:parent.resolvedSource; live:parent.resolvedSource !== null; visible:parent.resolvedSource !== null }
}
