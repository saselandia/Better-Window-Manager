// SPDX-License-Identifier: GPL-2.0-or-later
pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
Singleton {
 id:root
 property var state: ({layout:"thumbnail_grid",lookAndFeel:"org.kde.breeze.desktop",lockSource:"",osdSource:"",switcherSource:""})
 readonly property string configDir: Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME")+"/.config"
 function refresh() { debounce.restart(); }
 Timer {id:debounce;interval:120;onTriggered:if(!reader.running) reader.running=true;else debounce.restart()}
 Process {
  id:reader
  command:["python3",Quickshell.env("HOME")+"/.config/hypr/skins/plasma/scripts/interface-theme.py"]
  stdout:StdioCollector {onStreamFinished:{try {root.state=JSON.parse(text);}catch(e){console.warn("Plasma interface theme:",e);}}}
 }
 Component.onCompleted:refresh()
 FileView {path:root.configDir+"/kwinrc";watchChanges:true;printErrors:false;onFileChanged:{reload();root.refresh();}}
 FileView {path:root.configDir+"/kdeglobals";watchChanges:true;printErrors:false;onFileChanged:{reload();root.refresh();}}
 FileView {path:root.configDir+"/kdedefaults/kwinrc";watchChanges:true;printErrors:false;onFileChanged:{reload();root.refresh();}}
 FileView {path:root.configDir+"/kdedefaults/kdeglobals";watchChanges:true;printErrors:false;onFileChanged:{reload();root.refresh();}}
}
