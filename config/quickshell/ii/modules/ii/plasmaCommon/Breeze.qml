pragma Singleton

import qs.modules.common
import QtQuick
import Quickshell

/**
 * Shared KDE Plasma Breeze Dark tokens for the Plasma-style applets
 * (Bluetooth, Networks…). Same palette as PlasmaKickoff / PlasmaBarContent.
 */
Singleton {
    readonly property color panelBg: "#f024292e"
    readonly property color headerBg: "#2a2e32"
    readonly property color border: "#2e353b"
    readonly property color accent: "#3daee9"
    readonly property color accentSubtle: "#283daee9"
    readonly property color accentBorder: "#803daee9"
    readonly property color text: "#eff0f1"
    readonly property color textMuted: "#a1a9b1"
    readonly property color hover: "#15ffffff"
    readonly property color buttonBg: "#31363b"
    readonly property color buttonBorder: "#4d5257"
    readonly property color inputBg: "#1c2024"
    readonly property color negative: "#da4453"
    readonly property color positive: "#27ae60"
    readonly property color neutral: "#f67400"
    readonly property string fontFamily: "Google Sans Flex"

    // Bundled Breeze Dark icons: assets/icons/breeze-dark/<group>/<name>.svg
    function icon(group, name) {
        return "file://" + Directories.assetsPath + "/icons/breeze-dark/" + group + "/" + name + ".svg";
    }
}
