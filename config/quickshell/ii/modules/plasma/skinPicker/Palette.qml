pragma Singleton

import qs.modules.common
import qs.modules.plasma.theme
import QtQuick
import Quickshell

/**
 * Tokens de los applets Breeze actuales (Bluetooth, red, audio, Kickoff, panel…). Desde la fase 1
 * de docs/BREEZE_PLAN.md es una fachada sobre PlasmaTheme: los colores salen del esquema de color
 * de Plasma activo, no de una paleta Breeze Dark fija. Los applets portados de Plasma (fases 3–5)
 * usarán PlasmaTheme, Kirigami y KSvg directamente.
 */
Singleton {
    function alpha(c, a) {
        return Qt.rgba(c.r, c.g, c.b, a);
    }

    readonly property color panelBg: alpha(PlasmaTheme.windowBackground, 0.94)
    readonly property color headerBg: PlasmaTheme.headerBackground
    readonly property color border: Qt.tint(PlasmaTheme.windowBackground, alpha(PlasmaTheme.windowText, 0.12))
    readonly property color accent: PlasmaTheme.accent
    readonly property color accentSubtle: alpha(PlasmaTheme.accent, 0.16)
    readonly property color accentBorder: alpha(PlasmaTheme.accent, 0.5)
    readonly property color text: PlasmaTheme.windowText
    readonly property color textMuted: PlasmaTheme.inactiveText
    readonly property color hover: alpha(PlasmaTheme.windowText, 0.08)
    readonly property color buttonBg: PlasmaTheme.buttonBackground
    readonly property color buttonBorder: Qt.tint(PlasmaTheme.buttonBackground, alpha(PlasmaTheme.buttonText, 0.25))
    readonly property color inputBg: PlasmaTheme.viewBackground
    readonly property color negative: PlasmaTheme.negative
    readonly property color positive: PlasmaTheme.positive
    readonly property color neutral: PlasmaTheme.neutral
    readonly property string fontFamily: PlasmaTheme.fontMain

}
