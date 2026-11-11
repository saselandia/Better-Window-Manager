// SPDX-License-Identifier: GPL-2.0-or-later
// BWM: Plasma 6.7.5 OsdWindow host; OsdItem.qml is the upstream content.
import QtQuick
import "." as Local
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs.modules.plasma.runtime
import org.kde.ksvg as KSvg
PanelWindow {
    id: root
    property alias osdValue: content.osdValue
    property alias osdMaxValue: content.osdMaxValue
    property alias osdAdditionalText: content.osdAdditionalText
    property alias icon: content.icon
    property alias showingProgress: content.showingProgress
    property alias timeout: content.timeout
    property bool opened: false
    visible: opened
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    exclusiveZone: 0
    anchors.bottom: true
    margins.bottom: 80
    WlrLayershell.namespace: "bwm-plasma-osd"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    mask: Region {}
    implicitWidth: Math.max(300,content.implicitWidth+frame.margins.left+frame.margins.right)
    implicitHeight: content.implicitHeight+frame.margins.top+frame.margins.bottom
    function display(iconName,value,maximum,text,progress) {
        icon=iconName;osdValue=value;osdMaxValue=maximum;osdAdditionalText=text;showingProgress=progress;
        opened=true;hideTimer.restart();
    }
    function hide() {opened=false;hideTimer.stop();}
    Timer {id:hideTimer;interval:content.timeout;onTriggered:root.opened=false}
    Timer {id:displayDebounce;interval:200;onTriggered:root.display("video-display",qsTr("Display configuration changed"),100,"",false)}
    FileView {
        path:(Quickshell.env("XDG_CONFIG_HOME")||Quickshell.env("HOME")+"/.config")+"/hypr/monitors_layout.json"
        watchChanges:true;printErrors:false
        onFileChanged:{reload();displayDebounce.restart();}
    }
    IpcHandler {
        target:"plasmaOsd"
        function displayText(text:string,iconName:string):void {root.display(iconName,text,100,"",false);}
        function hide():void {root.hide();}
    }
    Loader {
        id:themed;anchors.fill:parent
        active:InterfaceTheme.state.osdSource!==""
        source:active?Qt.resolvedUrl("ThemedOsd.qml"):""
        onLoaded:item.values=Qt.binding(()=>({osdValue:root.osdValue,osdMaxValue:root.osdMaxValue,osdAdditionalText:root.osdAdditionalText,icon:root.icon,showingProgress:root.showingProgress,timeout:root.timeout}))
    }
    KSvg.FrameSvgItem {
        visible:!(themed.item?.ready??false)
        id:frame;anchors.fill:parent;imagePath:"widgets/background"
        Local.OsdItem {
            id:content
            anchors {fill:parent;leftMargin:frame.margins.left;rightMargin:frame.margins.right;topMargin:frame.margins.top;bottomMargin:frame.margins.bottom}
        }
    }
}
