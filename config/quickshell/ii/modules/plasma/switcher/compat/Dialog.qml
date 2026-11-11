// SPDX-License-Identifier: GPL-2.0-or-later
// BWM: PlasmaCore.Dialog's mainItem inside the host layer; no extra xdg window or focus owner.
import QtQuick
import org.kde.ksvg as KSvg
Item {
 id:root
 property int location:0
 property int flags:0
 property int type:0
 property bool hideOnWindowDeactivate:false
 property Item mainItem
 property alias margins:frame.margins
 readonly property real leftPadding:frame.margins.left
 readonly property real rightPadding:frame.margins.right
 readonly property real topPadding:frame.margins.top
 readonly property real bottomPadding:frame.margins.bottom
 width:(mainItem?.width??0)+frame.margins.left+frame.margins.right
 height:(mainItem?.height??0)+frame.margins.top+frame.margins.bottom
 signal sceneGraphError()
 onMainItemChanged:if(mainItem){mainItem.parent=root;mainItem.x=frame.margins.left;mainItem.y=frame.margins.top;}
 KSvg.FrameSvgItem {id:frame;anchors.fill:parent;imagePath:"dialogs/background";z:-1}
}
