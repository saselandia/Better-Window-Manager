pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import qs.Ui as OmarchyUi

// One section ("left", "center", "right") of Omarchy bar plugins inside the Retro bar. Each
// widget gets the same `bar` object omarchy-shell gives third-party plugins
// (Ui/PluginBarApi.qml): bar colours and size, `run`, tooltips/popout bookkeeping and
// `shell` (OmarchyPlugins). Popups are the plugins' own PopupCard windows.
Row {
    id: root

    required property string section
    property color foreground: "white"
    property color background: "black"
    property color urgent: "red"
    property string fontFamily: "JetBrainsMono Nerd Font"
    property int barSize: 26

    spacing: 4
    visible: repeater.count > 0

    Repeater {
        id: repeater
        model: OmarchyPlugins.entriesFor(root.section)

        delegate: Item {
            id: slot
            required property var modelData

            implicitWidth: loader.item ? loader.item.implicitWidth : 0
            implicitHeight: root.barSize
            width: implicitWidth
            height: root.barSize

            OmarchyUi.PluginBarApi {
                id: api
                pluginId: slot.modelData.id
                moduleName: slot.modelData.id
                shell: OmarchyPlugins
                foreground: root.foreground
                barForeground: root.foreground
                background: root.background
                urgent: root.urgent
                fontFamily: root.fontFamily
                position: "top"
                vertical: false
                barSize: root.barSize
                layoutConfig: OmarchyPlugins.barConfig

                _run: command => Quickshell.execDetached(["sh", "-c", command])
                _moduleWidgets: id => (loader.item ? [loader.item] : [])
                _requestPopout: owner => {
                    api.activePopout = owner;
                }
                _releasePopout: owner => {
                    if (api.activePopout === owner)
                        api.activePopout = null;
                }
                _targetBelongsToWindow: (target, window) => !!target && target.QsWindow?.window === window
            }

            Loader {
                id: loader
                anchors.verticalCenter: parent.verticalCenter
                height: root.barSize
                source: slot.modelData.source
                asynchronous: true
                onStatusChanged: {
                    if (status === Loader.Error)
                        console.warn(`[OmarchyPlugins] ${slot.modelData.id}: widget failed to load`);
                }
                onLoaded: {
                    item.bar = api;
                    item.settings = slot.modelData.settings;
                    if ("fixedEdge" in item)
                        item.fixedEdge = root.section === "left" ? "start" : (root.section === "right" ? "end" : "center");
                }
            }
        }
    }
}
