/*
    SPDX-FileCopyrightText: 2026 BWM
    SPDX-License-Identifier: GPL-2.0-or-later
*/
pragma Singleton

import QtQuick
import Quickshell
import org.kde.plasma.core as PlasmaCore
import qs.modules.common
import qs.modules.plasma.panel

/**
 * BWM: sustituto del attached Plasmoid de libplasma para el Kickoff portado (fase 4 de
 * docs/BREEZE_PLAN.md). Fuera de un contenedor de Plasma no hay Applet: estas propiedades dan
 * lo que el QML de Kickoff lee de él. La configuración es la de applets/kickoff/main.xml, guardada
 * en bar.plasma.kickoff (Config.qml) en vez de en plasma-org.kde.plasma.desktop-appletsrc.
 */
Singleton {
    id: root

    // Cliente de favoritos de Kickoff en KActivities: org.kde.plasma.kickoff.favorites.instance-<id>
    // (las pruebas usan otro con BWM_KICKOFF_ID para no tocar los del usuario)
    readonly property string id: Quickshell.env("BWM_KICKOFF_ID") || "bwm"
    readonly property string title: KickoffI18n.i18n("Application Launcher")
    readonly property var configuration: Config.options.bar.plasma.kickoff
    readonly property string icon: configuration.icon ?? "start-here-kde-symbolic"
    readonly property int immutability: PlasmaCore.Types.Mutable
    property bool activationTogglesExpanded: true

    readonly property string edge: PanelState.edgeFor("")
    readonly property int location: ({ top: PlasmaCore.Types.TopEdge, left: PlasmaCore.Types.LeftEdge,
        right: PlasmaCore.Types.RightEdge })[edge] ?? PlasmaCore.Types.BottomEdge
    readonly property int formFactor: (edge === "left" || edge === "right") ? PlasmaCore.Types.Vertical : PlasmaCore.Types.Horizontal

    // Sin página de configuración propia de Kickoff (llegará con las Preferencias de F11)
    readonly property QtObject configureAction: QtObject {
        readonly property bool enabled: false
        readonly property string text: KickoffI18n.i18n("Configure Application Launcher…")
        function trigger() {}
    }
    function internalAction(name) {
        return name === "configure" ? configureAction : null;
    }
}
