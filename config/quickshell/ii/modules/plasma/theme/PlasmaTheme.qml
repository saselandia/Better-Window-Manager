pragma Singleton
pragma ComponentBehavior: Bound

import qs.modules.common
import qs.modules.common.functions
import QtQuick
import Quickshell
import Quickshell.Io

/**
 * Tema de Plasma activo para la skin Breeze, leído de los archivos reales de KDE (fase 1 de
 * docs/BREEZE_PLAN.md): esquema de color de ~/.config/kdeglobals (todos los grupos, como
 * KColorScheme), estilo de Plasma de plasmarc, tema de iconos y fuentes. Cambia en vivo cuando
 * plasma-theme.py, un KCM o un tema global reescriben esos archivos.
 *
 * Se lee con FileView (no con Kirigami) para que el singleton cargue aunque falten las bibliotecas
 * de KDE; los controles portados de Plasma (fase 3 en adelante) usan además Kirigami/KSvg, que
 * leen los mismos archivos.
 */
Singleton {
    id: root

    readonly property string configDir: FileUtils.trimFileProtocol(Directories.config)  // respeta XDG_CONFIG_HOME
    property var groups: ({})
    property var plasmarc: ({})

    // Valores por defecto de KColorScheme (Breeze Dark de Plasma 6.7.5) para lo que falte
    readonly property var fallback: ({
        "Colors:Window": { BackgroundNormal: "32,35,38", BackgroundAlternate: "41,44,48", ForegroundNormal: "252,252,252",
            ForegroundInactive: "161,169,177", ForegroundActive: "61,174,233", ForegroundLink: "29,153,243",
            ForegroundVisited: "155,89,182", ForegroundNegative: "218,68,83", ForegroundNeutral: "246,116,0",
            ForegroundPositive: "39,174,96", DecorationFocus: "61,174,233", DecorationHover: "61,174,233" },
        "Colors:View": { BackgroundNormal: "20,22,24", BackgroundAlternate: "29,31,34" },
        "Colors:Button": { BackgroundNormal: "41,44,48", BackgroundAlternate: "38,41,45" },
        "Colors:Selection": { BackgroundNormal: "61,174,233", ForegroundNormal: "252,252,252" },
        "Colors:Tooltip": { BackgroundNormal: "41,44,48" },
        "Colors:Complementary": { BackgroundNormal: "32,35,38" },
        "Colors:Header": { BackgroundNormal: "41,44,48" },
        "WM": { activeBackground: "39,44,49", activeForeground: "252,252,252", inactiveBackground: "32,36,40",
            inactiveForeground: "161,169,177" }
    })

    function parseIni(text) {
        const out = {};
        let section = "";
        for (const raw of (text || "").split("\n")) {
            const line = raw.trim();
            if (!line || line.startsWith("#") || line.startsWith(";"))
                continue;
            if (line.startsWith("[") && line.endsWith("]")) {
                section = line.slice(1, -1);
                if (!out[section])
                    out[section] = {};
                continue;
            }
            const eq = line.indexOf("=");
            if (eq > 0 && section)
                out[section][line.slice(0, eq).replace(/\[\$[a-z]+\]$/, "").trim()] = line.slice(eq + 1).trim();
        }
        return out;
    }

    function parseColor(value) {
        if (!value)
            return null;
        if (value.startsWith("#"))
            return value;
        const p = value.split(",").map(v => parseInt(v));
        if (p.length < 3 || p.some(isNaN))
            return null;
        return Qt.rgba(p[0] / 255, p[1] / 255, p[2] / 255, p.length > 3 ? p[3] / 255 : 1);
    }

    /// Color de un grupo y un rol de KColorScheme: color("View", "BackgroundNormal"), color("WM", "activeBackground")
    function color(group, role) {
        const section = group === "WM" ? "WM" : `Colors:${group}`;
        return parseColor(root.groups[section]?.[role])
            ?? (section !== "WM" ? parseColor(root.groups["Colors:Window"]?.[role]) : null)
            ?? parseColor(root.fallback[section]?.[role])
            ?? parseColor(root.fallback["Colors:Window"][role])
            ?? "#000000";
    }

    function fontFamily(spec, fallback) {
        // "Noto Sans,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
        return spec ? spec.split(",")[0] : fallback;
    }
    function fontSize(spec, fallback) {
        const size = spec ? parseFloat(spec.split(",")[1]) : NaN;
        return isNaN(size) ? fallback : size;
    }

    readonly property var general: root.groups["General"] ?? {}
    readonly property string colorScheme: general.ColorScheme ?? "BreezeLight"
    readonly property string desktopTheme: root.plasmarc["Theme"]?.name ?? "default"
    readonly property string iconTheme: root.groups["Icons"]?.Theme ?? "breeze"
    readonly property string lookAndFeel: root.groups["KDE"]?.LookAndFeelPackage ?? ""

    readonly property color windowBackground: color("Window", "BackgroundNormal")
    readonly property color windowAlternate: color("Window", "BackgroundAlternate")
    readonly property color windowText: color("Window", "ForegroundNormal")
    readonly property color inactiveText: color("Window", "ForegroundInactive")
    readonly property color viewBackground: color("View", "BackgroundNormal")
    readonly property color viewText: color("View", "ForegroundNormal")
    readonly property color buttonBackground: color("Button", "BackgroundNormal")
    readonly property color buttonText: color("Button", "ForegroundNormal")
    readonly property color headerBackground: color("Header", "BackgroundNormal")
    readonly property color headerText: color("Header", "ForegroundNormal")
    readonly property color tooltipBackground: color("Tooltip", "BackgroundNormal")
    readonly property color tooltipText: color("Tooltip", "ForegroundNormal")
    readonly property color complementaryBackground: color("Complementary", "BackgroundNormal")
    readonly property color selectionBackground: color("Selection", "BackgroundNormal")
    readonly property color selectionText: color("Selection", "ForegroundNormal")
    readonly property color accent: (general.accentColorFromWallpaper !== "true" && parseColor(general.AccentColor)) || selectionBackground
    readonly property color focus: color("Window", "DecorationFocus")
    readonly property color hoverDecoration: color("Window", "DecorationHover")
    readonly property color link: color("Window", "ForegroundLink")
    readonly property color negative: color("Window", "ForegroundNegative")
    readonly property color neutral: color("Window", "ForegroundNeutral")
    readonly property color positive: color("Window", "ForegroundPositive")
    readonly property bool dark: (0.2126 * windowBackground.r + 0.7152 * windowBackground.g + 0.0722 * windowBackground.b) < 0.5

    // Fuentes de Plasma ([General] de kdeglobals); sin ellas, las de la skin
    readonly property string defaultFont: Appearance.font?.family?.main ?? "Google Sans Flex"
    readonly property string fontMain: fontFamily(general.font, defaultFont)
    readonly property real fontMainSize: fontSize(general.font, 10)
    readonly property string fontFixed: fontFamily(general.fixed, Appearance.font?.family?.monospace ?? "monospace")
    readonly property string fontSmall: fontFamily(general.smallestReadableFont, fontMain)
    readonly property real fontSmallSize: fontSize(general.smallestReadableFont, 8)

    FileView {
        path: `${root.configDir}/kdeglobals`
        watchChanges: true
        onFileChanged: reload()
        onLoaded: root.groups = root.parseIni(text())
        onLoadFailed: root.groups = {}
    }

    FileView {
        path: `${root.configDir}/plasmarc`
        watchChanges: true
        onFileChanged: reload()
        onLoaded: root.plasmarc = root.parseIni(text())
        onLoadFailed: root.plasmarc = {}
    }
}
