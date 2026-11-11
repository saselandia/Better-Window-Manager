import QtQuick
import QtQuick.Effects
import Quickshell
import qs
import qs.services
import qs.modules.common
import qs.modules.common.panels.lock
import qs.modules.ii.plasmaCommon

// Bloqueo de la skin Breeze (Kde plasma), como la pantalla de bloqueo Breeze de Plasma 6
// (lookandfeel/contents/lockscreen): en reposo, el fondo de escritorio con el reloj grande en el
// centro; al mover el ratón o pulsar una tecla, el fondo se desenfoca y oscurece, el reloj sube y
// aparecen el avatar, el nombre y el campo de contraseña con el botón de desbloquear. Sin
// actividad vuelve al reposo. Diseño propio de BWM que imita Breeze, no código de KDE.
MouseArea {
    id: root
    required property LockContext context

    property bool uiShown: false
    readonly property string userName: Quickshell.env("USER") ?? ""
    readonly property string faceIcon: "file://" + Quickshell.env("HOME") + "/.face.icon"
    readonly property string faceFile: "file://" + Quickshell.env("HOME") + "/.face"

    function wake() {
        root.uiShown = true;
        hideTimer.restart();
        root.context.resetClearTimer();
        if (!password.input.activeFocus)
            Qt.callLater(() => password.input.forceActiveFocus());
    }

    hoverEnabled: true
    onPositionChanged: root.wake()
    onPressed: root.wake()
    Component.onCompleted: password.input.forceActiveFocus()

    Connections {
        target: root.context
        function onShouldReFocus() {
            password.input.forceActiveFocus();
        }
        function onCurrentTextChanged() {
            if (password.text !== root.context.currentText)
                password.text = root.context.currentText;
        }
    }
    Connections {
        target: GlobalStates
        function onScreenUnlockFailedChanged() {
            if (GlobalStates.screenUnlockFailed)
                root.wake();
        }
    }

    // Sin actividad (y sin contraseña a medias), vuelve al reloj solo
    Timer {
        id: hideTimer
        interval: 10000
        onTriggered: if (password.text.length === 0 && !root.context.unlockInProgress) root.uiShown = false
    }

    Rectangle {
        anchors.fill: parent
        color: "#1b1e20"
    }

    Image {
        id: wallpaper
        anchors.fill: parent
        source: Config.options.background.wallpaperPath
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        cache: false
        sourceSize: Qt.size(root.width, root.height)
        visible: false
    }

    // WallpaperFader de Plasma: desenfoca y oscurece el fondo cuando se muestra el formulario
    MultiEffect {
        anchors.fill: wallpaper
        source: wallpaper
        visible: wallpaper.status === Image.Ready
        autoPaddingEnabled: false
        blurEnabled: true
        blurMax: 64
        blur: root.uiShown ? 1 : 0
        brightness: root.uiShown ? -0.25 : 0
        Behavior on blur { NumberAnimation { duration: 250; easing.type: Easing.InOutQuad } }
        Behavior on brightness { NumberAnimation { duration: 250; easing.type: Easing.InOutQuad } }
    }

    // Reloj (time + date) del lockscreen Breeze, con sombra suave
    Column {
        id: clock
        anchors.horizontalCenter: parent.horizontalCenter
        y: root.uiShown ? root.height * 0.16 : (root.height - height) / 2
        spacing: 0
        Behavior on y { NumberAnimation { duration: 250; easing.type: Easing.InOutQuad } }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: DateTime.time
            color: Breeze.text
            font.family: Breeze.fontFamily
            font.pixelSize: Math.round(root.height * 0.09)
            font.weight: Font.Light
            layer.enabled: true
            layer.effect: MultiEffect { shadowEnabled: true; shadowBlur: 0.6; shadowColor: "#80000000"; shadowVerticalOffset: 1 }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.locale().toString(DateTime.clock.date, Qt.locale().dateFormat(Locale.LongFormat))
            color: Breeze.text
            font.family: Breeze.fontFamily
            font.pixelSize: Math.round(root.height * 0.022)
            layer.enabled: true
            layer.effect: MultiEffect { shadowEnabled: true; shadowBlur: 0.6; shadowColor: "#80000000"; shadowVerticalOffset: 1 }
        }
    }

    // Avatar, nombre y contraseña
    Column {
        id: form
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: clock.bottom
        anchors.topMargin: root.height * 0.07
        spacing: 14
        opacity: root.uiShown ? 1 : 0
        // Sólo se atenúa, nunca se oculta: un elemento invisible pierde el foco y la primera
        // tecla en reposo no llegaría al campo (en Plasma ya escribe la contraseña).
        Behavior on opacity { NumberAnimation { duration: 250 } }

        Rectangle {
            id: avatar
            anchors.horizontalCenter: parent.horizontalCenter
            width: 128
            height: 128
            radius: width / 2
            color: Breeze.buttonBg
            border.width: 2
            border.color: Breeze.text
            clip: true

            Image {
                id: face
                anchors.fill: parent
                anchors.margins: 2
                source: root.faceIcon
                fillMode: Image.PreserveAspectCrop
                visible: false
                onStatusChanged: if (status === Image.Error && source.toString() === root.faceIcon) source = root.faceFile
            }
            MultiEffect {
                anchors.fill: face
                source: face
                visible: face.status === Image.Ready
                maskEnabled: true
                maskSource: faceMask
            }
            Item {
                id: faceMask
                anchors.fill: face
                visible: false
                layer.enabled: true
                Rectangle { anchors.fill: parent; radius: width / 2 }
            }
            Text {
                anchors.centerIn: parent
                visible: face.status !== Image.Ready
                text: root.userName.slice(0, 1).toUpperCase()
                color: Breeze.text
                font.family: Breeze.fontFamily
                font.pixelSize: 56
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.userName
            color: Breeze.text
            font.family: Breeze.fontFamily
            font.pixelSize: 20
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 6

            BreezeTextField {
                id: password
                width: 260
                height: 34
                echoMode: TextInput.Password
                placeholder: root.context.unlockInProgress ? "Desbloqueando…" : "Contraseña"
                input.enabled: !root.context.unlockInProgress
                input.font.pixelSize: 14
                input.inputMethodHints: Qt.ImhSensitiveData
                onTextChanged: {
                    root.context.currentText = text;
                    if (text.length > 0) root.wake();
                }
                onAccepted: if (text.length > 0) root.context.tryUnlock(false)
                onEscapePressed: root.context.currentText = ""
            }

            Rectangle {
                width: 34
                height: 34
                radius: 4
                color: unlockArea.containsMouse ? Breeze.hover : Breeze.buttonBg
                border.width: 1
                border.color: unlockArea.containsMouse ? Breeze.accent : Breeze.buttonBorder

                Image {
                    anchors.centerIn: parent
                    width: 22
                    height: 22
                    sourceSize: Qt.size(22, 22)
                    source: Breeze.icon("lock", "go-next")
                }
                MouseArea {
                    id: unlockArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: if (password.text.length > 0) root.context.tryUnlock(false)
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: GlobalStates.screenUnlockFailed
            text: "No se pudo desbloquear"
            color: Breeze.text
            font.family: Breeze.fontFamily
            font.pixelSize: 14
        }
    }

    // Pie: batería (en portátiles), como el de la pantalla de bloqueo de Plasma
    Text {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 18
        visible: Battery.available && root.uiShown
        text: Math.round(Battery.percentage * 100) + " %"
        color: Breeze.text
        font.family: Breeze.fontFamily
        font.pixelSize: 14
    }
}
