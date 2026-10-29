import qs.modules.common
import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls

/**
 * Material 3 styled TextArea (filled style)
 * https://m3.material.io/components/text-fields/overview
 * Note: We don't use NativeRendering because it makes the small placeholder text look weird
 */
TextArea {
    id: root
    Material.theme: Material.System
    Material.accent: Appearance.m3colors.m3primary
    Material.primary: Appearance.m3colors.m3primary
    Material.background: Appearance.m3colors.m3surface
    Material.foreground: Appearance.m3colors.m3onSurface
    Material.containerStyle: Material.Filled
    renderType: Text.QtRendering
    color: Appearance.colors.colOnLayer0
    selectByMouse: true
    leftPadding: 12
    rightPadding: 12
    topPadding: 10
    bottomPadding: 10

    selectedTextColor: Appearance.m3colors.m3onSecondaryContainer
    selectionColor: Appearance.colors.colSecondaryContainer
    placeholderTextColor: Appearance.m3colors.m3outline

    background: Rectangle {
        implicitHeight: 56
        color: Appearance.m3colors.m3surface
        topLeftRadius: Math.min(4, Appearance.rounding.verysmall)
        topRightRadius: Math.min(4, Appearance.rounding.verysmall)
        border.width: Appearance.outlinedControls ? (root.activeFocus ? 2 : 1) : 0
        border.color: root.activeFocus ? Appearance.colors.colPrimary : Appearance.m3colors.m3outlineVariant
        Rectangle {
            visible: !Appearance.outlinedControls
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: 1
            color: root.focus ? Appearance.m3colors.m3primary : 
                root.hovered ? Appearance.m3colors.m3outline : Appearance.m3colors.m3outlineVariant

            Behavior on color {
                animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
            }
        }
    }

    font {
        family: Appearance.font.family.main
        pixelSize: Appearance?.font.pixelSize.small ?? 15
        hintingPreference: Font.PreferFullHinting
        variableAxes: Appearance.font.variableAxes.main
    }
    wrapMode: TextEdit.Wrap
}
