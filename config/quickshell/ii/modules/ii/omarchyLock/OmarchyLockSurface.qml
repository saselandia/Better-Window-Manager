import QtQuick
import qs
import qs.modules.common
import qs.modules.common.panels.lock
import qs.Commons as Commons

// Bloqueo de la skin Retro: la vista de Omarchy 4 (LockView.qml, copia sin cambios: fondo
// desenfocado y un único campo de contraseña con su borde y textos) sobre el bloqueo de BWM
// (LockContext: PAM, huella, llavero). El fondo es el de Retro (background.wallpaperPath).
Item {
    id: root
    required property LockContext context
    property int attempts: 0

    Connections {
        target: root.context
        function onShouldReFocus() {
            view.forcePasswordFocus();
        }
    }
    Connections {
        target: GlobalStates
        function onScreenUnlockFailedChanged() {
            if (GlobalStates.screenUnlockFailed)
                root.attempts++;
        }
    }

    LockView {
        id: view
        anchors.fill: parent
        backgroundPath: Config.options.background.wallpaperPath
        fingerprintConfigured: root.context.fingerprintsConfigured
        authenticatingPassword: root.context.unlockInProgress
        failureMessage: GlobalStates.screenUnlockFailed ? Commons.I18n.t("lock.authenticationFailed").arg(root.attempts) : ""
        passwordText: root.context.currentText

        onPasswordTextEdited: password => root.context.currentText = password
        onSubmitPassword: password => {
            root.context.currentText = password;
            root.context.tryUnlock(false);
        }
        onClearFailureRequested: GlobalStates.screenUnlockFailed = false
        onWakeRequested: root.context.resetClearTimer()
    }
}
