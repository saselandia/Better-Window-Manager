import QtQuick
import Qt5Compat.GraphicalEffects
import qs
import qs.services
import qs.modules.common
import qs.modules.common.functions
import qs.modules.common.panels.lock

// Retro theme lock screen, a copy of Omarchy's hyprlock.conf (MIT): the wallpaper blurred,
// and a single square password box in the middle with a thick border, monospace text and
// the "Enter Password" placeholder; the border takes the accent colour while checking.
// Colours come from the Omarchy palette (Appearance in Retro is rendered from it).
MouseArea {
    id: root
    required property LockContext context
    property int attempts: 0

    readonly property color bg: Appearance.m3colors.m3background
    readonly property color fg: Appearance.m3colors.m3onBackground
    readonly property color accent: Appearance.m3colors.m3primary
    readonly property string mono: Appearance.font.family.monospace

    function forceFieldFocus() {
        passwordBox.forceActiveFocus();
    }
    Connections {
        target: root.context
        function onShouldReFocus() {
            root.forceFieldFocus();
        }
        function onCurrentTextChanged() {
            passwordBox.text = root.context.currentText;
        }
    }
    Connections {
        target: GlobalStates
        function onScreenUnlockFailedChanged() {
            if (GlobalStates.screenUnlockFailed)
                root.attempts++;
        }
    }
    hoverEnabled: true
    onPressed: forceFieldFocus()
    onPositionChanged: forceFieldFocus()
    Component.onCompleted: forceFieldFocus()

    // background { path = wallpaper; blur_passes = 3 }
    Rectangle {
        anchors.fill: parent
        color: root.bg
    }
    Image {
        id: wallpaper
        anchors.fill: parent
        source: Config.options.background.wallpaperPath
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        visible: false
    }
    FastBlur {
        anchors.fill: parent
        source: wallpaper
        radius: 64
        visible: wallpaper.status === Image.Ready
    }

    // input-field { size = 650, 100; outline_thickness = 4; rounding = 0; font_size = 32 }
    Rectangle {
        id: field
        anchors.centerIn: parent
        width: 650
        height: 100
        radius: 0
        color: ColorUtils.transparentize(root.bg, 0.2)
        border.width: 4
        border.color: root.context.unlockInProgress ? root.accent
            : GlobalStates.screenUnlockFailed ? Appearance.m3colors.m3error : root.fg

        TextInput {
            id: passwordBox
            anchors.fill: parent
            anchors.leftMargin: 24
            anchors.rightMargin: 24
            verticalAlignment: TextInput.AlignVCenter
            horizontalAlignment: TextInput.AlignHCenter
            clip: true
            color: root.fg
            selectionColor: root.accent
            font.family: root.mono
            font.pixelSize: 32
            echoMode: TextInput.Password
            passwordCharacter: "•"
            inputMethodHints: Qt.ImhSensitiveData
            enabled: !root.context.unlockInProgress
            cursorVisible: false
            cursorDelegate: Item {}

            onTextChanged: root.context.currentText = text
            onAccepted: root.context.tryUnlock(false)
            Keys.onPressed: event => {
                root.context.resetClearTimer();
                if (event.key === Qt.Key_Escape)
                    root.context.currentText = "";
            }
        }

        // placeholder_text = "  Enter Password 󰈷 "; fail_text = "<i>$FAIL ($ATTEMPTS)</i>"
        Text {
            anchors.centerIn: parent
            visible: passwordBox.text.length === 0
            textFormat: Text.StyledText
            text: GlobalStates.screenUnlockFailed
                ? `<i>${Translation.tr("Incorrect password")} (${root.attempts})</i>`
                : "  " + Translation.tr("Enter password") + " 󰈷 "
            color: GlobalStates.screenUnlockFailed ? Appearance.m3colors.m3error : ColorUtils.transparentize(root.fg, 0.4)
            font.family: root.mono
            font.pixelSize: 32
        }

    }
}
