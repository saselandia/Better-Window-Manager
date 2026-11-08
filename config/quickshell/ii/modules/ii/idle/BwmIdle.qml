import qs
import qs.services
import qs.modules.common
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Mpris
import Quickshell.Wayland

/**
 * Inactividad, común a todas las skins (hace de hypridle). Los tiempos (Config.options.idle,
 * segundos, 0 = nunca; Ajustes → Inactividad) son los mismos en todas:
 *   screensaverTime: salvapantallas de la skin que lo trae (skins/<id>/scripts/launch-screensaver.sh:
 *                    Retro, como Omarchy), si idle.screensaver. Cualquier entrada lo cierra
 *   screen:  apaga las pantallas (DPMS); cualquier entrada las enciende
 *   lock:    bloquea con el bloqueo de la skin (IPC lock activate)
 *   suspend: suspende con bwm-power (que bloquea antes)
 * Respetan «mantener despierto» y las apps que inhiben el reposo (vídeo a pantalla completa…).
 * Un reproductor MPRIS sonando impide el salvapantallas y la suspensión, no apagar las pantallas
 * ni bloquear.
 * IPC: quickshell -c ii ipc call screensaver start|stop
 */
Scope {
    id: root

    readonly property string home: Quickshell.env("HOME")
    readonly property string skin: Config.options?.appearance?.bwmTheme ?? "default"
    readonly property string launcher: root.home + "/.config/hypr/skins/" + root.skin + "/scripts/launch-screensaver.sh"
    readonly property string powerCommand: root.home + "/.config/hypr/scripts/bwm-power"

    readonly property int screensaverSeconds: Config.options?.idle?.screensaverTime ?? 150
    readonly property int screenSeconds: Config.options?.idle?.screen ?? 300
    readonly property int lockSeconds: Config.options?.idle?.lock ?? 600
    readonly property int suspendSeconds: Config.options?.idle?.suspend ?? 0
    // Salvapantallas sólo si la skin trae uno y está activado
    property bool skinHasScreensaver: false
    readonly property bool useScreensaver: root.skinHasScreensaver && (Config.options?.idle?.screensaver ?? true)

    // «Mantener despierto» (indicador de la barra, menú de Retro)
    readonly property bool awake: Idle.inhibit
    // Any MPRIS player playing (music, a video in the browser...)
    readonly property bool mediaPlaying: Mpris.players.values.some(p => p.isPlaying)

    property bool running: false
    property bool screenIsOff: false

    function start(force) {
        if (GlobalStates.screenLocked) return;
        root.running = true;
        Quickshell.execDetached(force ? [root.launcher, "force"] : [root.launcher]);
    }
    function stop() {
        root.running = false;
        // "--" first: otherwise pkill reads the pattern as an option of its own
        Quickshell.execDetached(["pkill", "-f", "--", "class=org\\.bwm\\.screensaver"]);
        // The native one (Omarchy 4.5) closes itself on input; SIGTERM fades it and restores the cursor
        Quickshell.execDetached(["pkill", "-f", "--", "omarchy-screensaver/bin/omarchy-launch-screensaver"]);
    }
    function setScreens(on) {
        root.screenIsOff = !on;
        Quickshell.execDetached(["hyprctl", "dispatch", `hl.dsp.dpms({ action = "${on ? "enable" : "disable"}" })`]);
    }

    // ¿Trae salvapantallas la skin activa?
    Process {
        id: screensaverCheck
        command: ["test", "-x", root.launcher]
        onExited: exitCode => root.skinHasScreensaver = exitCode === 0
    }
    onLauncherChanged: screensaverCheck.running = true
    Component.onCompleted: screensaverCheck.running = true

    // Closes the screensaver on the first input once it is showing, also when started by hand
    // (the monitors below only notice activity after a real idle period)
    IdleMonitor {
        enabled: root.running
        timeout: 2
        respectInhibitors: false
        onIsIdleChanged: if (!isIdle && root.running) root.stop()
    }

    // Salvapantallas de la skin
    IdleMonitor {
        enabled: root.useScreensaver && root.screensaverSeconds > 0 && !root.awake && !root.mediaPlaying
        timeout: Math.max(1, root.screensaverSeconds)
        respectInhibitors: true
        onIsIdleChanged: {
            if (isIdle) root.start(false);
            else if (root.running) root.stop();
        }
    }

    // Pantallas apagadas (con el salvapantallas puesto, también lo cierra: no sigue dibujando a oscuras)
    IdleMonitor {
        enabled: root.screenSeconds > 0 && !root.awake
        timeout: Math.max(1, root.screenSeconds)
        respectInhibitors: true
        onIsIdleChanged: {
            if (isIdle) {
                if (root.running) root.stop();
                root.setScreens(false);
            } else if (root.screenIsOff) {
                root.setScreens(true);
            }
        }
        // «Mantener despierto» o un tiempo cambiado con la pantalla apagada: se vuelve a encender
        onEnabledChanged: if (!enabled && root.screenIsOff) root.setScreens(true)
    }

    IdleMonitor {
        enabled: root.lockSeconds > 0 && !root.awake
        timeout: Math.max(1, root.lockSeconds)
        respectInhibitors: true
        onIsIdleChanged: {
            if (!isIdle || GlobalStates.screenLocked) return;
            if (root.running) root.stop();
            Quickshell.execDetached(["quickshell", "-c", "ii", "ipc", "call", "lock", "activate"]);
        }
    }

    IdleMonitor {
        enabled: root.suspendSeconds > 0 && !root.awake && !root.mediaPlaying
        timeout: Math.max(1, root.suspendSeconds)
        respectInhibitors: true
        onIsIdleChanged: {
            if (isIdle) Quickshell.execDetached([root.powerCommand, "suspend"]);
        }
    }

    IpcHandler {
        target: "screensaver"
        function start(): void { root.start(true); }
        function stop(): void { root.stop(); }
    }
}
