pragma Singleton
import Quickshell
import qs.services
import qs.modules.common

Singleton {
    id: root

    // BWM: apagar/reiniciar/cerrar sesión/suspender van por bwm-power, común a todas las skins
    // (cierra las apps con cortesía y espera a que guarden antes de apagar)
    readonly property string powerCommand: Quickshell.env("HOME") + "/.config/hypr/scripts/bwm-power"

    function closeAllWindows() {
        HyprlandData.windowList.map(w => w.pid).forEach(pid => {
            Quickshell.execDetached(["kill", pid]);
        });
    }

    function changePassword() {
        Quickshell.execDetached(["bash", "-c", `${Config.options.apps.changePassword}`]);
    }

    function lock() {
        Quickshell.execDetached(["loginctl", "lock-session"]);
    }

    function suspend() {
        Quickshell.execDetached([root.powerCommand, "suspend"]);
    }

    function logout() {
        Quickshell.execDetached([root.powerCommand, "logout"]);
    }

    function launchTaskManager() {
        Quickshell.execDetached(["bash", "-c", `${Config.options.apps.taskManager}`]);
    }

    function hibernate() {
        Quickshell.execDetached([root.powerCommand, "hibernate"]);
    }

    function poweroff() {
        Quickshell.execDetached([root.powerCommand, "shutdown"]);
    }

    function reboot() {
        Quickshell.execDetached([root.powerCommand, "reboot"]);
    }

    function rebootToFirmware() {
        Quickshell.execDetached([root.powerCommand, "firmware"]);
    }
}
