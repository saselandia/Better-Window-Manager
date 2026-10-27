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
    // Built-in Omarchy widgets of the Retro bar (the clock) are given here instead of coming
    // from the plugin catalog: [{ id, source, settings }]
    property var fixedEntries: null
    // Free width for the section's widgets that size themselves (omarchy-mpris), -1 = let them measure
    property real widthBudget: -1
    // Room for the whole section (-1 = unlimited): widgets that do not fit whole are hidden,
    // from the last one, instead of being cut in half
    property real maxWidth: -1
    readonly property int fittedCount: {
        const n = repeater.count;
        if (root.maxWidth < 0)
            return n;
        let used = 0;
        for (let i = 0; i < n; i++) {
            const w = repeater.itemAt(i)?.implicitWidth ?? 0;
            if (used + w > root.maxWidth)
                return i;
            used += w + (w > 0 ? root.spacing : 0);
        }
        return n;
    }
    property color foreground: "white"
    property color background: "black"
    property color urgent: "red"
    property string fontFamily: "JetBrainsMono Nerd Font"
    property int barSize: 26

    spacing: 4
    visible: repeater.count > 0

    Repeater {
        id: repeater
        model: root.fixedEntries ?? OmarchyPlugins.entriesFor(root.section)

        delegate: Item {
            id: slot
            required property var modelData
            required property int index
            // Keep the item measurable when it does not fit. Hiding its parent would
            // also make loader.item.visible false and create a fit/visibility loop.
            readonly property bool fits: index < root.fittedCount
            opacity: fits ? 1 : 0
            enabled: fits
            clip: !fits
            // What omarchy-shell's bar slots expose: plugins such as omarchy-mpris measure the
            // free space between slots (BarGeometry.js) through these two
            readonly property var activeItem: slot.fits && loader.item?.visible ? loader.item : null
            readonly property string region: root.section === "left" ? "left" : (root.section === "right" ? "right" : "center")
            readonly property real bwmWidthBudget: root.widthBudget

            // Invisible widgets (single keyboard layout, no updates/player...) must
            // release their space just like entries removed from the layout.
            implicitWidth: loader.item?.visible ? loader.item.implicitWidth : 0
            implicitHeight: root.barSize
            width: fits ? implicitWidth : 0
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

                // Omarchy commands the plugins run (omarchy-launch-*) come from BWM's stand-ins
                _run: command => Quickshell.execDetached(["sh", "-c", `PATH="$HOME/.config/hypr/scripts/omarchy-shims:$PATH"; ${command}`])
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
