pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Services.Polkit
import qs.modules.common

Singleton {
    id: root
    // Not in Retro: there Omarchy's own agent (modules/ii/omarchyPolkit) is the session's one, and
    // polkit only lets one agent register
    readonly property var agent: agentLoader.item
    readonly property bool active: agentLoader.item?.isActive ?? false
    readonly property var flow: agentLoader.item?.flow ?? null
    property bool interactionAvailable: false
    property string cleanMessage: {
        if (!root.flow) return "";
        return root.flow.message.endsWith(".")
            ? root.flow.message.slice(0, -1)
            : root.flow.message
    }
    property string cleanPrompt: {
        const inputPrompt = PolkitService.flow?.inputPrompt.trim() ?? "";
        const cleanedInputPrompt = inputPrompt.endsWith(":") ? inputPrompt.slice(0, -1) : inputPrompt;
        const usePasswordChars = !PolkitService.flow?.responseVisible ?? true
        return cleanedInputPrompt || (usePasswordChars ? Translation.tr("Password") : Translation.tr("Input"))
    }

    function cancel() {
        root.flow.cancelAuthenticationRequest()
    }

    function submit(string) {
        root.flow.submit(string)
        root.interactionAvailable = false
    }

    Connections {
        target: root.flow
        function onAuthenticationFailed() {
            root.interactionAvailable = true;
        }
    }

    LazyLoader {
        id: agentLoader
        active: Config.ready && !Appearance.isRetro
        PolkitAgent {
            onAuthenticationRequestStarted: {
                root.interactionAvailable = true;
            }
        }
    }
}
