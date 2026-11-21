// BWM: KSvg's "translucent" selector from QML. With KWin's blur effect active, libplasma sets the
// ImageSet selectors to {"translucent"} (ThemePrivate::updateKSvgSelectors, libplasma 6.7.5) and
// ImageSetPrivate::findInImageSet (KSvg 6.29.0) looks, theme by theme, for translucent/<path>
// before <path>. The selectors are not exposed to QML, so resolve the same order here: the
// current theme's translucent variant, else its plain one, else the fallback theme's translucent.
import QtQuick
import org.kde.ksvg as KSvg

QtObject {
    id: root
    required property string path
    // What to draw without blur (the caller keeps its previous choice, e.g. the solid variant)
    property string withoutBlur: path
    readonly property string resolved: !PlasmaTheme.blur ? withoutBlur
        : (translucent.fromCurrentImageSet || !plain.fromCurrentImageSet) ? "translucent/" + path : path
    readonly property KSvg.Svg translucent: KSvg.Svg { imagePath: "translucent/" + root.path }
    readonly property KSvg.Svg plain: KSvg.Svg { imagePath: root.path }
}
